"""Tests for FHIR R4 API endpoints."""

import base64
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimic_explorer.settings')
django.setup()

from pathlib import Path
from django.test import TestCase
from rest_framework.test import APIClient
from core.importer import MIMICImporter
from core.duckdb_manager import get_connection
from tests.duckdb_test_utils import DuckDBTestMixin

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'mimic-iv-test'


class FHIRTestBase(DuckDBTestMixin, TestCase):
    """Base class that imports test fixtures once for all FHIR tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_duckdb()
        importer = MIMICImporter(
            folder_path=str(FIXTURE_PATH),
            modules=['hosp'],
        )
        importer.run()
        cls.api = APIClient()
        conn = get_connection()
        row = conn.execute("SELECT subject_id, gender FROM patient LIMIT 1").fetchone()
        cls.patient_subject_id = row[0]
        cls.patient_gender = row[1]
        enc = conn.execute("SELECT hadm_id FROM encounter LIMIT 1").fetchone()
        cls.encounter_hadm_id = enc[0]

    @classmethod
    def tearDownClass(cls):
        cls._teardown_duckdb()
        super().tearDownClass()


class CapabilityStatementTest(FHIRTestBase):
    def test_capability_statement(self):
        """GET /fhir/metadata should return a valid FHIR CapabilityStatement."""
        resp = self.api.get('/fhir/metadata')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/metadata returned {resp.status_code}. The FHIR metadata "
            "endpoint may not be registered. Check fhir/urls.py for the 'metadata' "
            "path and fhir/views.py for the CapabilityStatement view."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'CapabilityStatement',
            "FHIR metadata should return resourceType='CapabilityStatement'. "
            "Check the CapabilityStatement view in fhir/views.py."
        )
        self.assertEqual(
            data['fhirVersion'], '4.0.1',
            "FHIR version should be '4.0.1' (R4). Check the CapabilityStatement "
            "construction in fhir/views.py."
        )
        resource_types = [r['type'] for r in data['rest'][0]['resource']]
        for rt in ['Patient', 'Encounter', 'Observation', 'Condition',
                    'Procedure', 'MedicationRequest', 'DocumentReference']:
            self.assertIn(
                rt, resource_types,
                f"CapabilityStatement is missing resource type '{rt}'. Check that "
                f"all supported resource types are listed in the CapabilityStatement "
                f"rest[0].resource array in fhir/views.py."
            )


class PatientReadTest(FHIRTestBase):
    def test_patient_read(self):
        """GET /fhir/Patient/:id/ should return a valid FHIR Patient resource."""
        resp = self.api.get(f'/fhir/Patient/mimic-{self.patient_subject_id}/')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/Patient/mimic-{self.patient_subject_id}/ returned "
            f"{resp.status_code}. Check that the FHIR Patient read view handles "
            "the 'mimic-<subject_id>' ID format correctly in fhir/views.py."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'Patient',
            "FHIR Patient read should return resourceType='Patient'. Check the "
            "Patient serialization in fhir/views.py or fhir/transformers.py."
        )
        self.assertEqual(
            data['id'], f'mimic-{self.patient_subject_id}',
            "FHIR Patient ID should be 'mimic-<subject_id>'. Check the ID "
            "generation in the FHIR Patient transformer."
        )
        self.assertIn(
            data['gender'], ('male', 'female'),
            f"FHIR Patient gender should be 'male' or 'female', got '{data.get('gender')}'. "
            "Check the gender mapping (M->male, F->female) in the FHIR transformer."
        )
        self.assertIn(
            'birthDate', data,
            "FHIR Patient should include a birthDate field (computed from "
            "anchor_age and anchor_year). Check the birthDate calculation."
        )
        self.assertEqual(
            len(data['identifier']), 1,
            "FHIR Patient should have exactly 1 identifier (the MIMIC subject_id). "
            "Check the identifier construction in the FHIR Patient transformer."
        )


class PatientSearchTest(FHIRTestBase):
    def test_patient_search_by_gender(self):
        """GET /fhir/Patient/?gender= should return a filtered Bundle."""
        gender_code = 'male' if self.patient_gender == 'M' else 'female'
        resp = self.api.get(f'/fhir/Patient/?gender={gender_code}')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/Patient/?gender={gender_code} returned {resp.status_code}. "
            "Check the Patient search view handles the 'gender' parameter."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'Bundle',
            "FHIR search should return a Bundle. Check the search view response."
        )
        self.assertEqual(
            data['type'], 'searchset',
            "FHIR search Bundle type should be 'searchset'."
        )
        self.assertGreater(
            data['total'], 0,
            f"No patients found for gender={gender_code}. The test fixtures should "
            "contain patients of both genders."
        )
        for entry in data['entry']:
            self.assertEqual(
                entry['resource']['gender'], gender_code,
                f"Patient gender filter returned a patient with gender "
                f"'{entry['resource']['gender']}' instead of '{gender_code}'. "
                "Check the gender filter in the FHIR Patient search view."
            )


class EncounterReadTest(FHIRTestBase):
    def test_encounter_read(self):
        """GET /fhir/Encounter/:id/ should return a valid FHIR Encounter."""
        resp = self.api.get(f'/fhir/Encounter/mimic-{self.encounter_hadm_id}/')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/Encounter/mimic-{self.encounter_hadm_id}/ returned "
            f"{resp.status_code}. Check the FHIR Encounter read view."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'Encounter',
            "Expected resourceType='Encounter'. Check FHIR Encounter serialization."
        )
        self.assertEqual(
            data['id'], f'mimic-{self.encounter_hadm_id}',
            "FHIR Encounter ID should be 'mimic-<hadm_id>'."
        )
        self.assertEqual(
            data['status'], 'finished',
            "FHIR Encounter status should be 'finished' for discharged encounters."
        )
        self.assertIn(
            'class', data,
            "FHIR Encounter should include a 'class' field (inpatient/emergency). "
            "Check the Encounter FHIR transformer."
        )
        self.assertIn(
            'period', data,
            "FHIR Encounter should include a 'period' with start/end times."
        )
        self.assertIn(
            'subject', data,
            "FHIR Encounter should include a 'subject' reference to the Patient."
        )


class ObservationSearchLabsTest(FHIRTestBase):
    def test_observation_search_labs(self):
        """GET /fhir/Observation/?category=laboratory should return lab results."""
        conn = get_connection()
        lab_count = conn.execute("SELECT COUNT(*) FROM lab_event").fetchone()[0]
        if lab_count == 0:
            self.skipTest('No lab events in fixtures')
        resp = self.api.get('/fhir/Observation/?category=laboratory')
        self.assertEqual(
            resp.status_code, 200,
            "GET /fhir/Observation/?category=laboratory failed. Check the "
            "Observation search view handles the 'category' filter."
        )
        data = resp.json()
        self.assertEqual(data['resourceType'], 'Bundle')
        self.assertGreater(
            data['total'], 0,
            "No lab observations found. LabEvent records exist in the DB but the "
            "FHIR Observation search returned 0. Check category filtering logic."
        )
        for entry in data['entry']:
            res = entry['resource']
            self.assertEqual(res['resourceType'], 'Observation')
            cat_code = res['category'][0]['coding'][0]['code']
            self.assertEqual(
                cat_code, 'laboratory',
                f"Observation category should be 'laboratory', got '{cat_code}'. "
                "Check the category mapping in the FHIR Observation transformer."
            )


class ObservationSearchVitalsTest(FHIRTestBase):
    def test_observation_search_vitals(self):
        """GET /fhir/Observation/?category=vital-signs should return vitals."""
        conn = get_connection()
        vital_count = conn.execute("SELECT COUNT(*) FROM vital_sign").fetchone()[0]
        if vital_count == 0:
            self.skipTest('No vital signs in fixtures')
        resp = self.api.get('/fhir/Observation/?category=vital-signs')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['resourceType'], 'Bundle')
        self.assertGreater(
            data['total'], 0,
            "No vital sign observations found despite VitalSign records existing."
        )
        for entry in data['entry']:
            cat_code = entry['resource']['category'][0]['coding'][0]['code']
            self.assertEqual(
                cat_code, 'vital-signs',
                f"Observation category should be 'vital-signs', got '{cat_code}'."
            )


class ConditionReadTest(FHIRTestBase):
    def test_condition_read(self):
        """GET /fhir/Condition/:id/ should return a FHIR Condition (diagnosis)."""
        conn = get_connection()
        row = conn.execute("""
            SELECT e.hadm_id, d.seq_num
            FROM diagnosis d
            JOIN encounter e ON d.encounter_id = e.id
            LIMIT 1
        """).fetchone()
        if not row:
            self.skipTest('No diagnoses in fixtures')
        hadm_id, seq_num = row
        fhir_id = f'mimic-dx-{hadm_id}-{seq_num}'
        resp = self.api.get(f'/fhir/Condition/{fhir_id}/')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/Condition/{fhir_id}/ returned {resp.status_code}. Check "
            "that the Condition read view parses the 'mimic-dx-<hadm_id>-<seq_num>' "
            "ID format correctly."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'Condition',
            "Expected resourceType='Condition' for a diagnosis."
        )
        self.assertEqual(data['id'], fhir_id)
        self.assertIn(
            'coding', data['code'],
            "FHIR Condition should have code.coding with ICD code. Check the "
            "Condition FHIR transformer."
        )
        self.assertIn(
            'system', data['code']['coding'][0],
            "FHIR Condition coding should include a 'system' URI (ICD-9 or ICD-10)."
        )


class ProcedureReadTest(FHIRTestBase):
    def test_procedure_read(self):
        """GET /fhir/Procedure/:id/ should return a FHIR Procedure."""
        conn = get_connection()
        row = conn.execute("""
            SELECT e.hadm_id, p.seq_num
            FROM procedure p
            JOIN encounter e ON p.encounter_id = e.id
            LIMIT 1
        """).fetchone()
        if not row:
            self.skipTest('No procedures in fixtures')
        hadm_id, seq_num = row
        fhir_id = f'mimic-proc-{hadm_id}-{seq_num}'
        resp = self.api.get(f'/fhir/Procedure/{fhir_id}/')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/Procedure/{fhir_id}/ returned {resp.status_code}. Check "
            "the Procedure read view ID parsing."
        )
        data = resp.json()
        self.assertEqual(data['resourceType'], 'Procedure')
        self.assertEqual(
            data['status'], 'completed',
            "FHIR Procedure status should be 'completed'."
        )
        self.assertIn(
            'code', data,
            "FHIR Procedure should include a 'code' field with the ICD procedure code."
        )


class MedicationRequestReadTest(FHIRTestBase):
    def test_medication_request_read(self):
        """GET /fhir/MedicationRequest/:id/ should return a FHIR MedicationRequest."""
        conn = get_connection()
        row = conn.execute("SELECT id FROM medication LIMIT 1").fetchone()
        if not row:
            self.skipTest('No medications in fixtures')
        med_pk = row[0]
        fhir_id = f'mimic-med-{med_pk}'
        resp = self.api.get(f'/fhir/MedicationRequest/{fhir_id}/')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/MedicationRequest/{fhir_id}/ returned {resp.status_code}. "
            "Check the MedicationRequest read view."
        )
        data = resp.json()
        self.assertEqual(data['resourceType'], 'MedicationRequest')
        self.assertEqual(
            data['status'], 'completed',
            "FHIR MedicationRequest status should be 'completed'."
        )
        self.assertEqual(
            data['intent'], 'order',
            "FHIR MedicationRequest intent should be 'order'."
        )
        self.assertIn(
            'medicationCodeableConcept', data,
            "FHIR MedicationRequest should include 'medicationCodeableConcept' with "
            "the drug name. Check the MedicationRequest transformer."
        )


class DocumentReferenceReadTest(FHIRTestBase):
    def test_document_reference_read(self):
        """GET /fhir/DocumentReference/:id/ should return a FHIR DocumentReference."""
        conn = get_connection()
        row = conn.execute("SELECT note_id, text FROM note LIMIT 1").fetchone()
        if not row:
            self.skipTest('No notes in fixtures')
        note_id = row[0]
        note_text = row[1]
        fhir_id = f'mimic-note-{note_id}'
        resp = self.api.get(f'/fhir/DocumentReference/{fhir_id}/')
        self.assertEqual(
            resp.status_code, 200,
            f"GET /fhir/DocumentReference/{fhir_id}/ returned {resp.status_code}. "
            "Check the DocumentReference read view."
        )
        data = resp.json()
        self.assertEqual(data['resourceType'], 'DocumentReference')
        self.assertEqual(
            data['status'], 'current',
            "FHIR DocumentReference status should be 'current'."
        )
        self.assertIn(
            'content', data,
            "FHIR DocumentReference should include 'content' with an attachment."
        )
        attachment = data['content'][0]['attachment']
        self.assertEqual(
            attachment['contentType'], 'text/plain',
            "DocumentReference attachment contentType should be 'text/plain'."
        )
        # Verify base64 content decodes to original text
        decoded = base64.b64decode(attachment['data']).decode('utf-8')
        self.assertEqual(
            decoded, note_text,
            "DocumentReference base64 attachment did not decode to the original "
            "note text. Check the base64 encoding in the DocumentReference transformer."
        )


class PatientEverythingTest(FHIRTestBase):
    def test_patient_everything(self):
        """GET /fhir/Patient/:id/$everything should return a Bundle of all resources."""
        resp = self.api.get(f'/fhir/Patient/mimic-{self.patient_subject_id}/$everything')
        self.assertEqual(
            resp.status_code, 200,
            f"Patient $everything returned {resp.status_code}. Check the "
            "$everything view in fhir/views.py."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'Bundle',
            "$everything should return a FHIR Bundle."
        )
        self.assertGreater(
            len(data['entry']), 0,
            "$everything returned an empty Bundle. It should contain at least the "
            "Patient resource plus any associated Encounters, Observations, etc."
        )
        resource_types = {e['resource']['resourceType'] for e in data['entry']}
        self.assertIn(
            'Patient', resource_types,
            "$everything Bundle should include the Patient resource itself."
        )


class FHIR404Test(FHIRTestBase):
    def test_fhir_404(self):
        """Requesting a non-existent FHIR resource should return OperationOutcome."""
        resp = self.api.get('/fhir/Patient/mimic-9999999/')
        self.assertEqual(
            resp.status_code, 404,
            "A non-existent Patient should return 404. Check the FHIR Patient "
            "read view's error handling."
        )
        data = resp.json()
        self.assertEqual(
            data['resourceType'], 'OperationOutcome',
            "FHIR 404 responses should return an OperationOutcome resource, not a "
            "generic error. Check the error response in the FHIR views."
        )
        self.assertEqual(
            data['issue'][0]['severity'], 'error',
            "OperationOutcome issue severity should be 'error' for 404s."
        )
