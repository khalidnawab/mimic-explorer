import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')
django.setup()

from django.test import TestCase
from core.models import SystemConfig
from core.duckdb_manager import get_connection
from clinical.models import VITAL_SIGN_ITEMIDS
from research.models import SavedQuery, CohortDefinition, CohortMember
from tests.duckdb_test_utils import DuckDBTestMixin


class SystemConfigTest(TestCase):
    def test_singleton(self):
        """SystemConfig should always return the same row (singleton pattern)."""
        config1 = SystemConfig.get_solo()
        config2 = SystemConfig.get_solo()
        self.assertEqual(
            config1.pk, config2.pk,
            "SystemConfig.get_solo() returned different rows — the singleton model "
            "is broken. Check that core/models.py SystemConfig.get_solo() creates or "
            "retrieves a single row with pk=1."
        )

    def test_default_values(self):
        """A fresh SystemConfig should have sensible defaults."""
        config = SystemConfig.get_solo()
        self.assertEqual(
            config.import_status, 'not_started',
            "Default import_status should be 'not_started'. Check the default value "
            "on SystemConfig.import_status field in core/models.py."
        )
        self.assertEqual(
            config.total_patients, 0,
            "Default total_patients should be 0. Check SystemConfig field defaults."
        )
        self.assertEqual(
            config.import_progress, {},
            "Default import_progress should be an empty dict. Check the JSONField "
            "default on SystemConfig.import_progress."
        )

    def test_update_status(self):
        """SystemConfig fields should persist after save and refresh."""
        config = SystemConfig.get_solo()
        config.import_status = 'in_progress'
        config.save()
        config.refresh_from_db()
        self.assertEqual(
            config.import_status, 'in_progress',
            "import_status did not persist after save/refresh. Check that the "
            "SystemConfig model and database migrations are applied correctly."
        )


class PatientModelTest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self._reset_duckdb()

    def test_create_patient(self):
        """Should be able to insert a patient into DuckDB and query it back."""
        conn = get_connection()
        conn.execute("""
            INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group)
            VALUES (10001, 'M', 65, 2150, '2017 - 2019')
        """)
        count = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        self.assertEqual(
            count, 1,
            "Expected exactly 1 patient in the database after inserting one."
        )
        row = conn.execute("SELECT subject_id, gender FROM patient WHERE subject_id = 10001").fetchone()
        self.assertEqual(row[0], 10001)
        self.assertEqual(row[1], 'M')

    def test_patient_with_dod(self):
        """Patient date-of-death field should store and return a value."""
        conn = get_connection()
        conn.execute("""
            INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group, dod)
            VALUES (10002, 'F', 72, 2180, '2017 - 2019', '2180-06-15')
        """)
        row = conn.execute("SELECT dod FROM patient WHERE subject_id = 10002").fetchone()
        self.assertIsNotNone(
            row[0],
            "Patient dod was None after setting it to '2180-06-15'."
        )

    def test_unique_subject_id(self):
        """Creating two patients with the same subject_id should raise an error."""
        conn = get_connection()
        conn.execute("""
            INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group)
            VALUES (10001, 'M', 65, 2150, 'test')
        """)
        with self.assertRaises(
            Exception,
            msg="Creating a duplicate subject_id should raise an error. "
                "Check that the patient table has a UNIQUE constraint on subject_id."
        ):
            conn.execute("""
                INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group)
                VALUES (10001, 'F', 45, 2150, 'test')
            """)


class EncounterModelTest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self._reset_duckdb()
        conn = get_connection()
        conn.execute("""
            INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group)
            VALUES (10001, 'M', 65, 2150, '2017 - 2019')
        """)

    def test_create_encounter(self):
        """Should create an encounter linked to a patient."""
        conn = get_connection()
        pid = conn.execute("SELECT id FROM patient WHERE subject_id = 10001").fetchone()[0]
        conn.execute(f"""
            INSERT INTO encounter (patient_id, hadm_id, admittime, admission_type)
            VALUES ({pid}, 20001, '2150-03-15 08:00:00', 'EMERGENCY')
        """)
        count = conn.execute("SELECT COUNT(*) FROM encounter WHERE patient_id = ?", [pid]).fetchone()[0]
        self.assertEqual(
            count, 1,
            "Patient should have 1 encounter."
        )


class ClinicalModelTest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self._reset_duckdb()
        conn = get_connection()
        conn.execute("""
            INSERT INTO patient (subject_id, gender, anchor_age, anchor_year, anchor_year_group)
            VALUES (10001, 'M', 65, 2150, 'test')
        """)
        pid = conn.execute("SELECT id FROM patient WHERE subject_id = 10001").fetchone()[0]
        conn.execute(f"""
            INSERT INTO encounter (patient_id, hadm_id, admittime, admission_type)
            VALUES ({pid}, 20001, '2150-03-15 08:00:00', 'EMERGENCY')
        """)

    def test_create_lab_event(self):
        """Should create a LabEvent in DuckDB."""
        conn = get_connection()
        pid = conn.execute("SELECT id FROM patient WHERE subject_id = 10001").fetchone()[0]
        eid = conn.execute("SELECT id FROM encounter WHERE hadm_id = 20001").fetchone()[0]
        conn.execute(f"""
            INSERT INTO lab_event (patient_id, encounter_id, labevent_id, itemid,
                label, charttime, valuenum, valueuom)
            VALUES ({pid}, {eid}, 1, 50912, 'Creatinine', '2150-03-15 09:00:00', 1.2, 'mg/dL')
        """)
        row = conn.execute("SELECT label FROM lab_event WHERE labevent_id = 1").fetchone()
        self.assertEqual(row[0], 'Creatinine')

    def test_create_diagnosis(self):
        """Should create a Diagnosis with correct ICD code."""
        conn = get_connection()
        pid = conn.execute("SELECT id FROM patient WHERE subject_id = 10001").fetchone()[0]
        eid = conn.execute("SELECT id FROM encounter WHERE hadm_id = 20001").fetchone()[0]
        conn.execute(f"""
            INSERT INTO diagnosis (patient_id, encounter_id, seq_num, icd_code,
                icd_version, long_title)
            VALUES ({pid}, {eid}, 1, 'I10', 10, 'Essential (primary) hypertension')
        """)
        row = conn.execute("SELECT icd_code FROM diagnosis WHERE encounter_id = ?", [eid]).fetchone()
        self.assertEqual(row[0], 'I10')

    def test_vital_sign_itemids(self):
        """The VITAL_SIGN_ITEMIDS lookup dict should contain Heart Rate."""
        self.assertIn(
            220045, VITAL_SIGN_ITEMIDS,
            "VITAL_SIGN_ITEMIDS is missing itemid 220045 (Heart Rate)."
        )
        self.assertEqual(VITAL_SIGN_ITEMIDS[220045], 'Heart Rate')

    def test_create_note(self):
        """Should create a clinical Note in DuckDB."""
        conn = get_connection()
        pid = conn.execute("SELECT id FROM patient WHERE subject_id = 10001").fetchone()[0]
        eid = conn.execute("SELECT id FROM encounter WHERE hadm_id = 20001").fetchone()[0]
        conn.execute(f"""
            INSERT INTO note (patient_id, encounter_id, note_id, note_type, text)
            VALUES ({pid}, {eid}, 'N001', 'discharge', 'Test discharge note')
        """)
        row = conn.execute("SELECT note_type FROM note WHERE note_id = 'N001'").fetchone()
        self.assertEqual(row[0], 'discharge')


class ResearchModelTest(TestCase):
    def test_create_saved_query(self):
        """Should create a SavedQuery with JSON definition."""
        sq = SavedQuery.objects.create(
            name='Test Query',
            query_definition={'type': 'diagnosis', 'code': 'I10'},
        )
        self.assertEqual(
            str(sq), 'Test Query',
            "SavedQuery __str__ should return the query name."
        )

    def test_create_cohort(self):
        """Should create a CohortDefinition with JSON criteria."""
        cohort = CohortDefinition.objects.create(
            name='Sepsis Cohort',
            criteria={'inclusion': [{'type': 'diagnosis', 'code_prefix': 'A41'}]},
        )
        self.assertEqual(
            str(cohort), 'Sepsis Cohort',
            "CohortDefinition __str__ should return the cohort name."
        )
