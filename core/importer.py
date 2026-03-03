"""
MIMIC-IV Data Import Pipeline.

Imports MIMIC-IV CSV files into DuckDB with native SQL,
progress tracking, and cancel support.
"""
import logging
import threading
from pathlib import Path

from django.utils import timezone

logger = logging.getLogger(__name__)

# Required files for import validation
REQUIRED_HOSP_FILES = [
    'hosp/patients',
    'hosp/admissions',
    'hosp/diagnoses_icd',
    'hosp/procedures_icd',
    'hosp/labevents',
    'hosp/prescriptions',
    'hosp/d_labitems',
    'hosp/d_icd_diagnoses',
    'hosp/d_icd_procedures',
]

OPTIONAL_HOSP_FILES = [
    'hosp/transfers',
    'hosp/emar',
    'hosp/emar_detail',
]

ICU_FILES = [
    'icu/icustays',
    'icu/chartevents',
    'icu/d_items',
]

NOTE_FILES = [
    'note/discharge',
    'note/radiology',
]


def validate_mimic_folder(folder_path):
    """
    Validate that a folder contains MIMIC-IV data files.
    Returns dict with 'required', 'optional', 'icu', 'note' file status.
    """
    folder = Path(folder_path)
    result = {
        'valid': True,
        'path': str(folder),
        'required': [],
        'optional': [],
        'icu': [],
        'note': [],
        'missing_required': [],
    }

    for f in REQUIRED_HOSP_FILES:
        found = _find_csv(folder, f)
        if found:
            result['required'].append({'file': f, 'found': True, 'path': str(found)})
        else:
            result['required'].append({'file': f, 'found': False})
            result['missing_required'].append(f)
            result['valid'] = False

    for f in OPTIONAL_HOSP_FILES:
        found = _find_csv(folder, f)
        result['optional'].append({'file': f, 'found': bool(found)})

    for f in ICU_FILES:
        found = _find_csv(folder, f)
        result['icu'].append({'file': f, 'found': bool(found)})

    for f in NOTE_FILES:
        found = _find_csv(folder, f)
        result['note'].append({'file': f, 'found': bool(found)})

    return result


def _find_csv(base_path, relative_name):
    """Try .csv.gz first, then .csv for a MIMIC file."""
    base = Path(base_path)
    for ext in ['.csv.gz', '.csv']:
        full = base / (relative_name + ext)
        if full.exists():
            return full
    return None


def _csv_path_sql(path):
    """Return a DuckDB-safe path string with forward slashes."""
    return str(path).replace('\\', '/')


class MIMICImporter:
    """
    Handles the full MIMIC-IV data import pipeline.
    Runs in a background thread with progress tracking and cancel support.
    Uses DuckDB native CSV reading for fast import.
    """

    STAGES = [
        'reference_tables',
        'patients',
        'admissions',
        'transfers',
        'icu_stays',
        'diagnoses',
        'procedures',
        'prescriptions',
        'labevents',
        'chartevents',
        'emar',
        'notes',
        'finalize',
    ]

    def __init__(self, folder_path, modules=None, patient_limit=None,
                 generate_fhir=False, cancel_event=None, existing_patients_only=False):
        self.folder_path = Path(folder_path)
        self.modules = modules or ['hosp']
        self.patient_limit = patient_limit
        self.generate_fhir = generate_fhir
        self.cancel_event = cancel_event or threading.Event()
        self.existing_patients_only = existing_patients_only
        self._active_stages = [s for s in self.STAGES if not (existing_patients_only and s == 'patients')]

    def _check_cancel(self):
        """Check if import has been cancelled."""
        if self.cancel_event.is_set():
            raise ImportCancelledError("Import was cancelled by user")

    def _update_progress(self, stage, percent=0, detail='', rows_imported=0):
        """Update import progress in SystemConfig."""
        from core.models import SystemConfig
        config = SystemConfig.get_solo()
        config.import_progress = {
            'stage': stage,
            'percent': percent,
            'detail': detail,
            'rows_imported': rows_imported,
            'stages_total': len(self._active_stages),
            'stage_index': self._active_stages.index(stage) if stage in self._active_stages else 0,
        }
        config.save(update_fields=['import_progress'])

    def _get_conn(self):
        """Get the DuckDB connection."""
        from core.duckdb_manager import get_connection
        return get_connection()

    def run(self):
        """Execute the full import pipeline."""
        from core.models import SystemConfig

        config = SystemConfig.get_solo()
        config.import_status = 'in_progress'
        config.import_started_at = timezone.now()
        config.import_progress = {}
        config.save()

        try:
            if self.existing_patients_only:
                conn = self._get_conn()
                count = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
                if count == 0:
                    raise ImportError("No existing patients found. Run a full import first.")

            self._import_reference_tables()
            if not self.existing_patients_only:
                self._import_patients()
            self._import_admissions()
            self._import_transfers()
            self._import_icu_stays()
            self._import_diagnoses()
            self._import_procedures()
            self._import_prescriptions()
            self._import_labevents()
            self._import_chartevents()
            self._import_emar()
            self._import_notes()
            self._finalize()

            config.refresh_from_db()
            config.import_status = 'completed'
            config.import_completed_at = timezone.now()
            config.save()

            logger.info("MIMIC import completed successfully")

        except ImportCancelledError:
            config.refresh_from_db()
            config.import_status = 'cancelled'
            config.save()
            logger.info("MIMIC import was cancelled")

        except Exception as e:
            config.refresh_from_db()
            config.import_status = 'failed'
            config.import_progress = {
                **config.import_progress,
                'error': str(e),
            }
            config.save()
            logger.exception("MIMIC import failed")
            raise

    def _import_reference_tables(self):
        """Stage 1: Load reference tables as DuckDB temp tables."""
        self._update_progress('reference_tables', 0, 'Loading reference tables...')
        self._check_cancel()

        conn = self._get_conn()

        # d_labitems
        path = _find_csv(self.folder_path, 'hosp/d_labitems')
        if path:
            conn.execute("DROP TABLE IF EXISTS _d_labitems")
            conn.execute(f"""
                CREATE TEMP TABLE _d_labitems AS
                SELECT * FROM read_csv('{_csv_path_sql(path)}', auto_detect=true)
            """)

        # d_icd_diagnoses
        path = _find_csv(self.folder_path, 'hosp/d_icd_diagnoses')
        if path:
            conn.execute("DROP TABLE IF EXISTS _d_icd_diagnoses")
            conn.execute(f"""
                CREATE TEMP TABLE _d_icd_diagnoses AS
                SELECT * FROM read_csv('{_csv_path_sql(path)}', auto_detect=true)
            """)

        # d_icd_procedures
        path = _find_csv(self.folder_path, 'hosp/d_icd_procedures')
        if path:
            conn.execute("DROP TABLE IF EXISTS _d_icd_procedures")
            conn.execute(f"""
                CREATE TEMP TABLE _d_icd_procedures AS
                SELECT * FROM read_csv('{_csv_path_sql(path)}', auto_detect=true)
            """)

        # d_items (for chartevents)
        if 'icu' in self.modules:
            path = _find_csv(self.folder_path, 'icu/d_items')
            if path:
                conn.execute("DROP TABLE IF EXISTS _d_items")
                conn.execute(f"""
                    CREATE TEMP TABLE _d_items AS
                    SELECT * FROM read_csv('{_csv_path_sql(path)}', auto_detect=true)
                """)

        self._update_progress('reference_tables', 100, 'Reference tables loaded')

    def _import_patients(self):
        """Stage 2: Import patients."""
        self._update_progress('patients', 0, 'Importing patients...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/patients')
        if path is None:
            raise ImportError("patients.csv not found")

        limit_clause = f"LIMIT {self.patient_limit}" if self.patient_limit else ""

        conn.execute(f"""
            INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group, dod)
            SELECT subject_id, gender, anchor_age, anchor_year, anchor_year_group,
                   TRY_CAST(dod AS DATE)
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true)
            {limit_clause}
            ON CONFLICT (subject_id) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        self._update_progress('patients', 100, f'Imported {count} patients')

    def _import_admissions(self):
        """Stage 3: Import admissions -> encounter."""
        self._update_progress('admissions', 0, 'Importing admissions...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/admissions')
        if path is None:
            raise ImportError("admissions.csv not found")

        conn.execute(f"""
            INSERT INTO encounter (patient_id, hadm_id, admittime, dischtime, deathtime,
                admission_type, admit_provider_id, admission_location, discharge_location,
                insurance, language, marital_status, race, edregtime, edouttime, hospital_expire_flag)
            SELECT
                p.id,
                a.hadm_id,
                TRY_CAST(a.admittime AS TIMESTAMP),
                TRY_CAST(a.dischtime AS TIMESTAMP),
                TRY_CAST(a.deathtime AS TIMESTAMP),
                COALESCE(a.admission_type, ''),
                COALESCE(CAST(a.admit_provider_id AS VARCHAR), ''),
                COALESCE(a.admission_location, ''),
                COALESCE(a.discharge_location, ''),
                COALESCE(a.insurance, ''),
                COALESCE(a.language, ''),
                COALESCE(a.marital_status, ''),
                COALESCE(a.race, ''),
                TRY_CAST(a.edregtime AS TIMESTAMP),
                TRY_CAST(a.edouttime AS TIMESTAMP),
                COALESCE(a.hospital_expire_flag, 0) = 1
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) a
            JOIN patient p ON a.subject_id = p.subject_id
            ON CONFLICT (hadm_id) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0]
        self._update_progress('admissions', 100, f'Imported {count} admissions')

    def _import_transfers(self):
        """Stage 4: Import transfers (optional)."""
        self._update_progress('transfers', 0, 'Importing transfers...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/transfers')
        if path is None:
            self._update_progress('transfers', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO transfer (patient_id, encounter_id, transfer_id, eventtype,
                careunit, intime, outtime)
            SELECT
                p.id,
                e.id,
                t.transfer_id,
                COALESCE(t.eventtype, ''),
                COALESCE(t.careunit, ''),
                TRY_CAST(t.intime AS TIMESTAMP),
                TRY_CAST(t.outtime AS TIMESTAMP)
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) t
            JOIN patient p ON t.subject_id = p.subject_id
            LEFT JOIN encounter e ON t.hadm_id = e.hadm_id
            ON CONFLICT (transfer_id) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM transfer").fetchone()[0]
        self._update_progress('transfers', 100, f'Imported {count} transfers')

    def _import_icu_stays(self):
        """Stage 5: Import ICU stays."""
        self._update_progress('icu_stays', 0, 'Importing ICU stays...')
        self._check_cancel()

        if 'icu' not in self.modules:
            self._update_progress('icu_stays', 100, 'Skipped (ICU module not selected)')
            return

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'icu/icustays')
        if path is None:
            self._update_progress('icu_stays', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO icu_stay (patient_id, encounter_id, stay_id,
                first_careunit, last_careunit, intime, outtime, los)
            SELECT
                p.id,
                e.id,
                i.stay_id,
                COALESCE(i.first_careunit, ''),
                COALESCE(i.last_careunit, ''),
                TRY_CAST(i.intime AS TIMESTAMP),
                TRY_CAST(i.outtime AS TIMESTAMP),
                TRY_CAST(i.los AS DOUBLE)
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) i
            JOIN patient p ON i.subject_id = p.subject_id
            JOIN encounter e ON i.hadm_id = e.hadm_id
            ON CONFLICT (stay_id) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM icu_stay").fetchone()[0]
        self._update_progress('icu_stays', 100, f'Imported {count} ICU stays')

    def _import_diagnoses(self):
        """Stage 6: Import diagnoses with reference lookup."""
        self._update_progress('diagnoses', 0, 'Importing diagnoses...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/diagnoses_icd')
        if path is None:
            self._update_progress('diagnoses', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO diagnosis (patient_id, encounter_id, seq_num, icd_code, icd_version, long_title)
            SELECT
                p.id,
                e.id,
                d.seq_num,
                CAST(d.icd_code AS VARCHAR),
                d.icd_version,
                COALESCE(ref.long_title, '')
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) d
            JOIN patient p ON d.subject_id = p.subject_id
            JOIN encounter e ON d.hadm_id = e.hadm_id
            LEFT JOIN _d_icd_diagnoses ref
                ON CAST(d.icd_code AS VARCHAR) = CAST(ref.icd_code AS VARCHAR)
                AND d.icd_version = ref.icd_version
            ON CONFLICT (encounter_id, seq_num) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM diagnosis").fetchone()[0]
        self._update_progress('diagnoses', 100, f'Imported {count} diagnoses')

    def _import_procedures(self):
        """Stage 7: Import procedures with reference lookup."""
        self._update_progress('procedures', 0, 'Importing procedures...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/procedures_icd')
        if path is None:
            self._update_progress('procedures', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO procedure (patient_id, encounter_id, seq_num, icd_code, icd_version, long_title)
            SELECT
                p.id,
                e.id,
                pr.seq_num,
                CAST(pr.icd_code AS VARCHAR),
                pr.icd_version,
                COALESCE(ref.long_title, '')
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) pr
            JOIN patient p ON pr.subject_id = p.subject_id
            JOIN encounter e ON pr.hadm_id = e.hadm_id
            LEFT JOIN _d_icd_procedures ref
                ON CAST(pr.icd_code AS VARCHAR) = CAST(ref.icd_code AS VARCHAR)
                AND pr.icd_version = ref.icd_version
            ON CONFLICT (encounter_id, seq_num) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM procedure").fetchone()[0]
        self._update_progress('procedures', 100, f'Imported {count} procedures')

    def _import_prescriptions(self):
        """Stage 8: Import prescriptions -> medication."""
        self._update_progress('prescriptions', 0, 'Importing prescriptions...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/prescriptions')
        if path is None:
            self._update_progress('prescriptions', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO medication (patient_id, encounter_id, pharmacy_id, poe_id,
                starttime, stoptime, drug_type, drug, gsn, ndc, prod_strength,
                form_rx, dose_val_rx, dose_unit_rx, form_val_disp, form_unit_disp,
                doses_per_24_hrs, route)
            SELECT
                p.id,
                e.id,
                TRY_CAST(rx.pharmacy_id AS INTEGER),
                COALESCE(CAST(rx.poe_id AS VARCHAR), ''),
                TRY_CAST(rx.starttime AS TIMESTAMP),
                TRY_CAST(rx.stoptime AS TIMESTAMP),
                COALESCE(rx.drug_type, ''),
                COALESCE(rx.drug, 'Unknown'),
                COALESCE(CAST(rx.gsn AS VARCHAR), ''),
                COALESCE(CAST(rx.ndc AS VARCHAR), ''),
                COALESCE(rx.prod_strength, ''),
                COALESCE(rx.form_rx, ''),
                COALESCE(CAST(rx.dose_val_rx AS VARCHAR), ''),
                COALESCE(rx.dose_unit_rx, ''),
                COALESCE(CAST(rx.form_val_disp AS VARCHAR), ''),
                COALESCE(rx.form_unit_disp, ''),
                TRY_CAST(rx.doses_per_24_hrs AS DOUBLE),
                COALESCE(rx.route, '')
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) rx
            JOIN patient p ON rx.subject_id = p.subject_id
            JOIN encounter e ON rx.hadm_id = e.hadm_id
            ON CONFLICT (encounter_id, pharmacy_id, drug, starttime) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM medication").fetchone()[0]
        self._update_progress('prescriptions', 100, f'Imported {count} medications')

    def _import_labevents(self):
        """Stage 9: Import labevents - single SQL statement."""
        self._update_progress('labevents', 0, 'Importing lab events...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/labevents')
        if path is None:
            self._update_progress('labevents', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO lab_event (patient_id, encounter_id, labevent_id, specimen_id,
                itemid, label, fluid, category, charttime, storetime,
                value, valuenum, valueuom, ref_range_lower, ref_range_upper,
                flag, priority, comments)
            SELECT
                p.id,
                e.id,
                l.labevent_id,
                TRY_CAST(l.specimen_id AS INTEGER),
                l.itemid,
                COALESCE(d.label, ''),
                COALESCE(d.fluid, ''),
                COALESCE(d.category, ''),
                TRY_CAST(l.charttime AS TIMESTAMP),
                TRY_CAST(l.storetime AS TIMESTAMP),
                CAST(l.value AS VARCHAR),
                TRY_CAST(l.valuenum AS DOUBLE),
                COALESCE(l.valueuom, ''),
                TRY_CAST(l.ref_range_lower AS DOUBLE),
                TRY_CAST(l.ref_range_upper AS DOUBLE),
                COALESCE(l.flag, ''),
                COALESCE(l.priority, ''),
                COALESCE(CAST(l.comments AS VARCHAR), '')
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true, ignore_errors=true) l
            JOIN patient p ON l.subject_id = p.subject_id
            LEFT JOIN encounter e ON l.hadm_id = e.hadm_id
            LEFT JOIN _d_labitems d ON l.itemid = d.itemid
            WHERE l.charttime IS NOT NULL
            ON CONFLICT (labevent_id) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM lab_event").fetchone()[0]
        self._update_progress('labevents', 100, f'Imported {count:,} lab events')

    def _import_chartevents(self):
        """Stage 10: Import chartevents -> vital_sign (filtered to vital sign itemids)."""
        self._update_progress('chartevents', 0, 'Importing vital signs...')
        self._check_cancel()

        if 'icu' not in self.modules:
            self._update_progress('chartevents', 100, 'Skipped (ICU module not selected)')
            return

        from clinical.models import VITAL_SIGN_ITEMIDS

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'icu/chartevents')
        if path is None:
            self._update_progress('chartevents', 100, 'Skipped (file not found)')
            return

        vital_itemids = list(VITAL_SIGN_ITEMIDS.keys())
        itemid_list = ', '.join(str(i) for i in vital_itemids)

        # Build a CASE expression for labels from VITAL_SIGN_ITEMIDS
        case_parts = []
        for itemid, label in VITAL_SIGN_ITEMIDS.items():
            case_parts.append(f"WHEN c.itemid = {itemid} THEN '{label}'")
        case_expr = "CASE " + " ".join(case_parts) + " ELSE COALESCE(di.label, '') END"

        # Check if _d_items temp table exists
        has_d_items = False
        try:
            conn.execute("SELECT 1 FROM _d_items LIMIT 0")
            has_d_items = True
        except Exception:
            pass

        d_items_join = "LEFT JOIN _d_items di ON c.itemid = di.itemid" if has_d_items else ""
        if not has_d_items:
            case_expr = "CASE " + " ".join(case_parts) + " ELSE '' END"

        conn.execute(f"""
            INSERT INTO vital_sign (patient_id, encounter_id, icu_stay_id, stay_id,
                charttime, itemid, label, value, valuenum, valueuom)
            SELECT
                p.id,
                e.id,
                icu.id,
                TRY_CAST(c.stay_id AS INTEGER),
                TRY_CAST(c.charttime AS TIMESTAMP),
                c.itemid,
                {case_expr},
                CAST(c.value AS VARCHAR),
                TRY_CAST(c.valuenum AS DOUBLE),
                COALESCE(c.valueuom, '')
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true, ignore_errors=true) c
            JOIN patient p ON c.subject_id = p.subject_id
            LEFT JOIN encounter e ON c.hadm_id = e.hadm_id
            LEFT JOIN icu_stay icu ON TRY_CAST(c.stay_id AS INTEGER) = icu.stay_id
            {d_items_join}
            WHERE c.itemid IN ({itemid_list})
              AND c.charttime IS NOT NULL
            ON CONFLICT (patient_id, stay_id, charttime, itemid) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM vital_sign").fetchone()[0]
        self._update_progress('chartevents', 100, f'Imported {count:,} vital signs')

    def _import_emar(self):
        """Stage 11: Import emar -> medication_administration (optional)."""
        self._update_progress('emar', 0, 'Importing medication administrations...')
        self._check_cancel()

        conn = self._get_conn()
        path = _find_csv(self.folder_path, 'hosp/emar')
        if path is None:
            self._update_progress('emar', 100, 'Skipped (file not found)')
            return

        conn.execute(f"""
            INSERT INTO medication_administration (patient_id, encounter_id, emar_id,
                pharmacy_id, charttime, medication, event_txt)
            SELECT
                p.id,
                e.id,
                COALESCE(CAST(em.emar_id AS VARCHAR), ''),
                TRY_CAST(em.pharmacy_id AS INTEGER),
                TRY_CAST(em.charttime AS TIMESTAMP),
                COALESCE(em.medication, ''),
                COALESCE(em.event_txt, '')
            FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) em
            JOIN patient p ON em.subject_id = p.subject_id
            LEFT JOIN encounter e ON em.hadm_id = e.hadm_id
            WHERE em.charttime IS NOT NULL
            ON CONFLICT (patient_id, emar_id) DO NOTHING
        """)

        count = conn.execute("SELECT COUNT(*) FROM medication_administration").fetchone()[0]
        self._update_progress('emar', 100, f'Imported {count} medication administrations')

    def _import_notes(self):
        """Stage 12: Import clinical notes (discharge + radiology)."""
        self._update_progress('notes', 0, 'Importing clinical notes...')
        self._check_cancel()

        if 'note' not in self.modules:
            self._update_progress('notes', 100, 'Skipped (Note module not selected)')
            return

        conn = self._get_conn()
        total_imported = 0

        for file_name, note_type in [('note/discharge', 'discharge'), ('note/radiology', 'radiology')]:
            self._check_cancel()

            path = _find_csv(self.folder_path, file_name)
            if path is None:
                continue

            conn.execute(f"""
                INSERT INTO note (patient_id, encounter_id, note_id, note_type,
                    note_seq, charttime, storetime, text)
                SELECT
                    p.id,
                    e.id,
                    CAST(n.note_id AS VARCHAR),
                    '{note_type}',
                    TRY_CAST(n.note_seq AS INTEGER),
                    TRY_CAST(n.charttime AS TIMESTAMP),
                    TRY_CAST(n.storetime AS TIMESTAMP),
                    COALESCE(n.text, '')
                FROM read_csv('{_csv_path_sql(path)}', auto_detect=true) n
                JOIN patient p ON n.subject_id = p.subject_id
                LEFT JOIN encounter e ON n.hadm_id = e.hadm_id
                ON CONFLICT (note_id) DO NOTHING
            """)

        total_imported = conn.execute("SELECT COUNT(*) FROM note").fetchone()[0]
        self._update_progress('notes', 100, f'Imported {total_imported} notes')

    def _finalize(self):
        """Stage 13: Update counts and mark import complete."""
        self._update_progress('finalize', 0, 'Finalizing import...')
        self._check_cancel()

        from core.models import SystemConfig

        conn = self._get_conn()
        total_patients = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        total_encounters = conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0]

        config = SystemConfig.get_solo()
        config.total_patients = total_patients
        config.total_encounters = total_encounters
        existing = config.imported_modules or []
        config.imported_modules = sorted(set(existing + self.modules))
        config.mimic_data_path = str(self.folder_path)
        config.save()

        self._update_progress('finalize', 100, 'Import finalized')


class ImportCancelledError(Exception):
    pass
