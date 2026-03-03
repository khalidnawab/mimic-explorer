import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')
django.setup()

from pathlib import Path
from django.test import TestCase
from core.importer import MIMICImporter, validate_mimic_folder
from core.models import SystemConfig
from core.duckdb_manager import get_connection
from tests.duckdb_test_utils import DuckDBTestMixin

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'mimic-iv-test'


class FolderValidationTest(TestCase):
    def test_valid_folder(self):
        """The test fixture folder should be detected as valid MIMIC-IV data."""
        result = validate_mimic_folder(str(FIXTURE_PATH))
        self.assertTrue(
            result['valid'],
            f"Fixture folder at {FIXTURE_PATH} was not detected as valid. "
            f"Missing required files: {result.get('missing_required', [])}. "
            "Make sure tests/fixtures/mimic-iv-test/hosp/ contains the required "
            "CSV files (patients.csv, admissions.csv, etc.)."
        )
        self.assertEqual(
            len(result['missing_required']), 0,
            f"Some required files are missing from the fixture folder: "
            f"{result['missing_required']}."
        )

    def test_invalid_folder(self):
        """A nonexistent path should fail validation."""
        result = validate_mimic_folder('/nonexistent/path')
        self.assertFalse(
            result['valid'],
            "A nonexistent folder should return valid=False."
        )
        self.assertGreater(
            len(result['missing_required']), 0,
            "An invalid folder should report missing required files."
        )

    def test_detects_icu_files(self):
        """Fixture folder should contain ICU module files."""
        result = validate_mimic_folder(str(FIXTURE_PATH))
        icu_found = {f['file']: f['found'] for f in result['icu']}
        self.assertTrue(
            icu_found.get('icu/icustays'),
            "icu/icustays.csv was not found in fixtures."
        )
        self.assertTrue(
            icu_found.get('icu/chartevents'),
            "icu/chartevents.csv was not found in fixtures."
        )

    def test_detects_note_files(self):
        """Fixture folder should contain Note module files."""
        result = validate_mimic_folder(str(FIXTURE_PATH))
        note_found = {f['file']: f['found'] for f in result['note']}
        self.assertTrue(
            note_found.get('note/discharge'),
            "note/discharge.csv was not found in fixtures."
        )


class ImportPipelineTest(DuckDBTestMixin, TestCase):
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
        # Reset SystemConfig for each test
        config = SystemConfig.get_solo()
        config.import_status = 'not_started'
        config.import_progress = {}
        config.imported_modules = []
        config.total_patients = 0
        config.total_encounters = 0
        config.save()

    def test_full_import(self):
        """Full import with all modules should complete and populate data."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp', 'icu', 'note'],
        )
        importer.run()

        config = SystemConfig.get_solo()
        self.assertEqual(
            config.import_status, 'completed',
            f"Import did not complete — status is '{config.import_status}'. "
            f"Progress: {config.import_progress}."
        )
        self.assertEqual(
            config.total_patients, 10,
            f"Expected 10 patients from fixtures, got {config.total_patients}."
        )
        self.assertGreater(
            config.total_encounters, 0,
            "No encounters were imported."
        )

    def test_patient_count(self):
        """Hosp-only import should create exactly 10 patients from fixtures."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        self.assertEqual(
            count, 10,
            f"Expected 10 patients, got {count}."
        )

    def test_encounter_count(self):
        """Hosp-only import should create exactly 12 encounters from fixtures."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0]
        self.assertEqual(
            count, 12,
            f"Expected 12 encounters, got {count}."
        )

    def test_patient_limit(self):
        """patient_limit=5 should import only 5 patients."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
            patient_limit=5,
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
        self.assertEqual(
            count, 5,
            f"Expected 5 patients with patient_limit=5, got {count}."
        )

    def test_lab_events(self):
        """Import should create lab events from labevents.csv."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM lab_event").fetchone()[0]
        self.assertGreater(
            count, 0,
            "No lab events were imported."
        )

    def test_diagnoses(self):
        """Import should create exactly 10 diagnoses from fixtures."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM diagnosis").fetchone()[0]
        self.assertEqual(
            count, 10,
            f"Expected 10 diagnoses, got {count}."
        )

    def test_icu_stays(self):
        """ICU module import should create ICU stays."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp', 'icu'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM icu_stay").fetchone()[0]
        self.assertGreater(
            count, 0,
            "No ICU stays were imported."
        )

    def test_vital_signs(self):
        """ICU module import should create vital signs from chartevents."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp', 'icu'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM vital_sign").fetchone()[0]
        self.assertGreater(
            count, 0,
            "No vital signs were imported."
        )

    def test_notes(self):
        """Note module import should create exactly 3 notes from fixtures."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp', 'note'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM note").fetchone()[0]
        self.assertEqual(
            count, 3,
            f"Expected 3 notes, got {count}."
        )

    def test_medications(self):
        """Import should create medications from prescriptions.csv."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        conn = get_connection()
        count = conn.execute("SELECT COUNT(*) FROM medication").fetchone()[0]
        self.assertGreater(
            count, 0,
            "No medications were imported."
        )

    def test_hosp_only_skips_icu(self):
        """Hosp-only import should NOT create ICU stays or vital signs."""
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        conn = get_connection()
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM icu_stay").fetchone()[0], 0,
            "ICU stays were created during a hosp-only import."
        )
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM vital_sign").fetchone()[0], 0,
            "Vital signs were created during a hosp-only import."
        )
