import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')
django.setup()

from pathlib import Path
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import SystemConfig
from core.importer import MIMICImporter
from core.duckdb_manager import get_connection
from research.models import CohortMember, CohortDefinition, SavedQuery
from tests.duckdb_test_utils import DuckDBTestMixin

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'mimic-iv-test'


class StatusAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_status_endpoint(self):
        """GET /api/status/ should return system configuration."""
        response = self.client.get('/api/status/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/status/ failed. This is the main status endpoint. Check that "
            "core/urls.py has a path for 'status/' and that StatusView in "
            "core/views.py returns the SystemConfig data."
        )
        self.assertIn(
            'import_status', response.json(),
            "Status response is missing 'import_status' field. Check the "
            "StatusView in core/views.py includes all fields."
        )
        self.assertEqual(
            response.json()['import_status'], 'not_started',
            "Fresh install should show import_status='not_started'. Check "
            "SystemConfig default values in core/models.py."
        )


class ValidateFolderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_validate_valid_folder(self):
        """POST /api/import/validate-folder/ should accept a valid MIMIC folder."""
        response = self.client.post(
            '/api/import/validate-folder/',
            {'folder_path': str(FIXTURE_PATH)},
            format='json',
        )
        self.assertEqual(
            response.status_code, 200,
            f"Folder validation returned {response.status_code}. Check that "
            "ValidateFolderView in core/views.py accepts POST with folder_path."
        )
        self.assertTrue(
            response.json()['valid'],
            f"Fixture folder was not detected as valid. Path: {FIXTURE_PATH}. "
            "Check that the fixture folder contains the required hosp/ CSV files."
        )

    def test_validate_invalid_folder(self):
        """POST /api/import/validate-folder/ should reject a nonexistent path."""
        response = self.client.post(
            '/api/import/validate-folder/',
            {'folder_path': '/nonexistent'},
            format='json',
        )
        self.assertEqual(
            response.status_code, 200,
            "Folder validation should return 200 even for invalid folders (with "
            "valid=false in the body), not an HTTP error."
        )
        self.assertFalse(
            response.json()['valid'],
            "Nonexistent folder should return valid=false."
        )


class PatientAPITest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()

    def test_patient_list(self):
        """GET /api/patients/ should return paginated patient list."""
        response = self.client.get('/api/patients/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/patients/ failed. Check patients/urls.py and patients/views.py "
            "for the patient list endpoint."
        )
        data = response.json()
        self.assertIn(
            'results', data,
            "Patient list response should be paginated with a 'results' key. "
            "Check that DRF pagination is configured in settings.py."
        )
        self.assertEqual(
            len(data['results']), 10,
            f"Expected 10 patients from fixtures, got {len(data['results'])}. "
            "The import may have failed or the fixture data may be incomplete."
        )

    def test_patient_filter_gender(self):
        """GET /api/patients/?gender=M should only return male patients."""
        response = self.client.get('/api/patients/', {'gender': 'M'})
        self.assertEqual(response.status_code, 200)
        for p in response.json()['results']:
            self.assertEqual(
                p['gender'], 'M',
                f"Gender filter returned a patient with gender '{p['gender']}'. "
                "Check the gender filter in the Patient list view."
            )

    def test_patient_detail(self):
        """GET /api/patients/:subject_id/ should return patient with encounters."""
        response = self.client.get('/api/patients/10001/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/patients/10001/ failed. Check the patient detail view uses "
            "subject_id (not pk) for lookup. The URL pattern should use "
            "<int:subject_id>."
        )
        data = response.json()
        self.assertEqual(
            data['subject_id'], 10001,
            "Patient detail returned wrong subject_id."
        )
        self.assertIn(
            'encounters', data,
            "Patient detail should include nested 'encounters'. Check the "
            "PatientDetailView includes encounters."
        )

    def test_patient_not_found(self):
        """GET /api/patients/99999/ should return 404 for unknown patient."""
        response = self.client.get('/api/patients/99999/')
        self.assertEqual(
            response.status_code, 404,
            "Non-existent patient should return 404. Check the patient detail "
            "view handles missing patients."
        )

    def test_encounter_list(self):
        """GET /api/encounters/ should return paginated encounter list."""
        response = self.client.get('/api/encounters/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/encounters/ failed. Check patients/urls.py for the "
            "encounters list endpoint."
        )
        self.assertIn(
            'results', response.json(),
            "Encounter list should be paginated with a 'results' key."
        )

    def test_encounter_detail(self):
        """GET /api/encounters/:hadm_id/ should return encounter details."""
        response = self.client.get('/api/encounters/20001/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/encounters/20001/ failed. Check the encounter detail view "
            "uses hadm_id for lookup."
        )
        self.assertEqual(
            response.json()['hadm_id'], 20001,
            "Encounter detail returned wrong hadm_id."
        )

    def test_encounter_labs(self):
        """GET /api/encounters/:hadm_id/labs/ should return lab events."""
        response = self.client.get('/api/encounters/20001/labs/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/encounters/20001/labs/ failed. Check that the encounter "
            "sub-resource URL for labs is registered in patients/urls.py."
        )

    def test_encounter_diagnoses(self):
        """GET /api/encounters/:hadm_id/diagnoses/ should return diagnoses."""
        response = self.client.get('/api/encounters/20001/diagnoses/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/encounters/20001/diagnoses/ failed. Check the encounter "
            "diagnoses sub-resource endpoint."
        )

    def test_patient_timeline(self):
        """GET /api/patients/:subject_id/timeline/ should return event list."""
        response = self.client.get('/api/patients/10001/timeline/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/patients/10001/timeline/ failed. Check the timeline view "
            "in patients/views.py."
        )
        self.assertIsInstance(
            response.json(), list,
            "Timeline endpoint should return a JSON array of events, not an object. "
            "Check the timeline view's Response format."
        )


class ClinicalAPITest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()

    def test_labs_list(self):
        """GET /api/labs/ should return paginated lab events."""
        response = self.client.get('/api/labs/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/labs/ failed. Check clinical/urls.py for the labs list "
            "endpoint and clinical/views.py for the view."
        )
        self.assertIn(
            'results', response.json(),
            "Labs list should be paginated with a 'results' key."
        )

    def test_labs_filter_patient(self):
        """GET /api/labs/?patient=10001 should filter by subject_id."""
        response = self.client.get('/api/labs/', {'patient': '10001'})
        self.assertEqual(
            response.status_code, 200,
            "GET /api/labs/?patient=10001 failed. Check that the labs view "
            "supports filtering by 'patient' (subject_id) parameter."
        )

    def test_diagnoses_list(self):
        """GET /api/diagnoses/ should return paginated diagnoses."""
        response = self.client.get('/api/diagnoses/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/diagnoses/ failed. Check clinical/urls.py for the diagnoses "
            "list endpoint."
        )

    def test_medications_list(self):
        """GET /api/medications/ should return paginated medications."""
        response = self.client.get('/api/medications/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/medications/ failed. Check clinical/urls.py for the "
            "medications list endpoint."
        )

    def test_lab_items(self):
        """GET /api/lab-items/ should return distinct lab item IDs."""
        response = self.client.get('/api/lab-items/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/lab-items/ failed. This endpoint should return a list of "
            "distinct {itemid, label} objects from imported lab events."
        )

    def test_vital_items(self):
        """GET /api/vital-items/ should return the list of tracked vital sign types."""
        response = self.client.get('/api/vital-items/')
        self.assertEqual(
            response.status_code, 200,
            "GET /api/vital-items/ failed. This endpoint returns the VITAL_SIGN_ITEMIDS "
            "mapping from clinical/models.py."
        )
        items = response.json()
        self.assertGreater(
            len(items), 0,
            "Vital items list is empty. This endpoint should return the "
            "VITAL_SIGN_ITEMIDS dict (13 vital sign types like Heart Rate, SpO2, etc.) "
            "regardless of whether any vitals have been imported."
        )


class ResetAPITest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()

    def test_reset_clears_all_data(self):
        """POST /api/reset/ should wipe all tables and reset config."""
        conn = get_connection()
        # Verify data exists before reset
        self.assertGreater(
            conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0], 0,
            "No patients in DB before reset test — the import may have failed."
        )
        self.assertGreater(
            conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0], 0,
            "No encounters in DB before reset test — the import may have failed."
        )
        config = SystemConfig.get_solo()
        self.assertEqual(config.import_status, 'completed')

        # Perform reset
        response = self.client.post('/api/reset/')
        self.assertEqual(
            response.status_code, 200,
            f"POST /api/reset/ returned {response.status_code}. Check ResetView "
            "in core/views.py."
        )
        self.assertEqual(
            response.json()['status'], 'reset_complete',
            "Reset response should return {status: 'reset_complete'}."
        )

        # Verify all DuckDB tables are empty
        for table, name in [
            ('patient', 'patients'), ('encounter', 'encounters'),
            ('icu_stay', 'ICU stays'), ('lab_event', 'lab events'),
            ('vital_sign', 'vital signs'), ('diagnosis', 'diagnoses'),
            ('procedure', 'procedures'), ('medication', 'medications'),
            ('note', 'notes'),
        ]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            self.assertEqual(
                count, 0,
                f"Reset did not clear {name} table ({count} rows remain). "
                f"Check that ResetView calls reset_all_tables() from duckdb_queries."
            )

        # Verify SQLite app-state tables are cleared
        self.assertEqual(
            CohortDefinition.objects.count(), 0,
            "Reset did not clear cohort definitions."
        )
        self.assertEqual(
            SavedQuery.objects.count(), 0,
            "Reset did not clear saved queries."
        )

        # Verify SystemConfig is reset
        config = SystemConfig.get_solo()
        self.assertEqual(
            config.import_status, 'not_started',
            "Reset should set import_status back to 'not_started'."
        )
        self.assertEqual(
            config.total_patients, 0,
            "Reset should set total_patients to 0."
        )
        self.assertEqual(
            config.total_encounters, 0,
            "Reset should set total_encounters to 0."
        )
        self.assertEqual(
            config.mimic_data_path, '',
            "Reset should clear mimic_data_path."
        )
        self.assertEqual(
            config.import_progress, {},
            "Reset should clear import_progress to {}."
        )
        self.assertEqual(
            config.imported_modules, [],
            "Reset should clear imported_modules to []."
        )


class SupplementImportAPITest(DuckDBTestMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()

    def test_supplement_import_requires_completed(self):
        """POST /api/import/supplement/ should return 400 if initial import not done."""
        config = SystemConfig.get_solo()
        config.import_status = 'not_started'
        config.save()

        response = self.client.post(
            '/api/import/supplement/',
            {
                'folder_path': str(FIXTURE_PATH),
                'modules': ['hosp', 'icu'],
                'patient_limit': 100,
                'generate_fhir': False,
            },
            format='json',
        )
        self.assertEqual(
            response.status_code, 400,
            "Supplement import should return 400 when import_status is not "
            "'completed'. You must complete an initial import before supplementing. "
            "Check SupplementImportView in core/views.py."
        )

        # Restore
        config.import_status = 'completed'
        config.save()

    def test_supplement_import_no_duplicates(self):
        """Re-importing the same data should not create duplicate rows."""
        conn = get_connection()
        patient_count_before = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        encounter_count_before = conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0]
        diagnosis_count_before = conn.execute("SELECT COUNT(*) FROM diagnosis").fetchone()[0]

        config = SystemConfig.get_solo()
        self.assertEqual(config.import_status, 'completed')
        self.assertEqual(
            config.imported_modules, ['hosp'],
            "Expected only 'hosp' in imported_modules before supplement test."
        )

        # Run supplement import synchronously (not via API thread)
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp', 'icu'],
        )
        importer.run()

        # Counts should not increase for hosp-only data
        patient_count_after = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        encounter_count_after = conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0]
        diagnosis_count_after = conn.execute("SELECT COUNT(*) FROM diagnosis").fetchone()[0]

        self.assertEqual(
            patient_count_after, patient_count_before,
            f"Patient count changed from {patient_count_before} to "
            f"{patient_count_after} after supplement import. Re-importing "
            "should be idempotent — check ON CONFLICT DO NOTHING on patient table."
        )
        self.assertEqual(
            encounter_count_after, encounter_count_before,
            f"Encounter count changed from {encounter_count_before} to "
            f"{encounter_count_after} after supplement import. Re-importing "
            "should be idempotent — check ON CONFLICT DO NOTHING on encounter table."
        )
        self.assertEqual(
            diagnosis_count_after, diagnosis_count_before,
            f"Diagnosis count changed from {diagnosis_count_before} to "
            f"{diagnosis_count_after} after supplement import. Duplicate "
            "diagnoses were created. Check UNIQUE constraint on diagnosis table."
        )

        # imported_modules should now include both
        config.refresh_from_db()
        self.assertIn(
            'hosp', config.imported_modules,
            "imported_modules should still contain 'hosp' after supplement."
        )
        self.assertIn(
            'icu', config.imported_modules,
            "imported_modules should contain 'icu' after supplementing with ICU data. "
            "Check that _finalize() in core/importer.py merges modules with existing."
        )

    def test_supplement_endpoint_starts(self):
        """POST /api/import/supplement/ should return 202 and complete in background."""
        config = SystemConfig.get_solo()
        config.import_status = 'completed'
        config.save()

        response = self.client.post(
            '/api/import/supplement/',
            {
                'folder_path': str(FIXTURE_PATH),
                'modules': ['hosp', 'icu'],
                'patient_limit': 100,
                'generate_fhir': False,
            },
            format='json',
        )
        self.assertEqual(
            response.status_code, 202,
            f"Supplement import returned {response.status_code}, expected 202. "
            "Check SupplementImportView in core/views.py returns HTTP_202_ACCEPTED."
        )
        self.assertEqual(
            response.json()['status'], 'started',
            "Supplement response should return {status: 'started'}."
        )

        # Wait for background thread to finish
        import time
        for _ in range(30):
            s = self.client.get('/api/import/status/').json()
            if s['import_status'] in ('completed', 'failed'):
                break
            time.sleep(0.5)

        config.refresh_from_db()
        self.assertEqual(
            config.import_status, 'completed',
            f"Supplement import did not complete — status is '{config.import_status}'. "
            f"Progress: {config.import_progress}. The background import thread may "
            "have failed. Check core/importer.py for errors."
        )
