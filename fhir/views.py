"""FHIR R4 API views — backed by DuckDB.

On-the-fly transformation from DuckDB data to FHIR JSON.
"""

from django.http import JsonResponse
from rest_framework.renderers import BaseRenderer
from rest_framework.views import APIView


class FHIRRenderer(BaseRenderer):
    """Accepts any content type — FHIR views return JsonResponse directly."""
    media_type = '*/*'
    format = 'fhir'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

from core.duckdb_queries import (
    get_fhir_patient, get_fhir_patients, get_fhir_encounter, get_fhir_encounters,
    get_fhir_lab, get_fhir_vital, get_fhir_labs, get_fhir_vitals,
    get_fhir_condition, get_fhir_conditions,
    get_fhir_procedure, get_fhir_procedures,
    get_fhir_medication, get_fhir_medications,
    get_fhir_note, get_fhir_notes,
    get_fhir_patient_everything,
)
from . import transformers


FHIR_CONTENT_TYPE = 'application/fhir+json'
PAGE_SIZE = 50


class FHIRView(APIView):
    """Base class for all FHIR views — bypasses DRF content negotiation."""
    renderer_classes = [FHIRRenderer]


def _parse_fhir_reference(value, resource_type):
    if value is None:
        return None
    value = str(value)
    if '/' in value:
        value = value.split('/')[-1]
    if value.startswith('mimic-'):
        value = value[6:]
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _fhir_json(data, status=200):
    return JsonResponse(data, status=status, content_type=FHIR_CONTENT_TYPE)


def _fhir_error(status, diagnostics):
    return _fhir_json({
        'resourceType': 'OperationOutcome',
        'issue': [{
            'severity': 'error',
            'code': 'not-found' if status == 404 else 'invalid',
            'diagnostics': diagnostics,
        }],
    }, status=status)


def _paginate_bundle(request, total, items, transformer, page_param='_page'):
    try:
        page = max(1, int(request.GET.get(page_param, 1)))
    except (ValueError, TypeError):
        page = 1

    entries = [transformer(item) for item in items]

    base_url = request.build_absolute_uri(request.path)
    params = request.GET.copy()
    links = [{'relation': 'self', 'url': request.build_absolute_uri()}]

    start = (page - 1) * PAGE_SIZE
    if start + PAGE_SIZE < total:
        params[page_param] = str(page + 1)
        links.append({'relation': 'next', 'url': f'{base_url}?{params.urlencode()}'})
    if page > 1:
        params[page_param] = str(page - 1)
        links.append({'relation': 'previous', 'url': f'{base_url}?{params.urlencode()}'})

    return _fhir_json(transformers.make_bundle(entries, total=total, links=links))


# ---------------------------------------------------------------------------
# CapabilityStatement
# ---------------------------------------------------------------------------

class CapabilityStatementView(FHIRView):
    def get(self, request):
        resources = [
            {
                'type': 'Patient',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': '_id', 'type': 'token'},
                    {'name': 'gender', 'type': 'token'},
                ],
            },
            {
                'type': 'Encounter',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': 'patient', 'type': 'reference'},
                    {'name': 'date', 'type': 'date'},
                ],
            },
            {
                'type': 'Observation',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': 'patient', 'type': 'reference'},
                    {'name': 'encounter', 'type': 'reference'},
                    {'name': 'category', 'type': 'token'},
                    {'name': 'code', 'type': 'token'},
                    {'name': 'date', 'type': 'date'},
                ],
            },
            {
                'type': 'Condition',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': 'patient', 'type': 'reference'},
                    {'name': 'encounter', 'type': 'reference'},
                    {'name': 'code', 'type': 'token'},
                ],
            },
            {
                'type': 'Procedure',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': 'patient', 'type': 'reference'},
                    {'name': 'encounter', 'type': 'reference'},
                ],
            },
            {
                'type': 'MedicationRequest',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': 'patient', 'type': 'reference'},
                    {'name': 'encounter', 'type': 'reference'},
                ],
            },
            {
                'type': 'DocumentReference',
                'interaction': [{'code': 'read'}, {'code': 'search-type'}],
                'searchParam': [
                    {'name': 'patient', 'type': 'reference'},
                    {'name': 'encounter', 'type': 'reference'},
                    {'name': 'type', 'type': 'token'},
                ],
            },
        ]

        statement = {
            'resourceType': 'CapabilityStatement',
            'status': 'active',
            'kind': 'instance',
            'fhirVersion': '4.0.1',
            'format': ['json'],
            'rest': [{
                'mode': 'server',
                'resource': resources,
                'operation': [{
                    'name': '$everything',
                    'definition': 'http://hl7.org/fhir/OperationDefinition/Patient-everything',
                }],
            }],
        }
        return _fhir_json(statement)


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

class PatientView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            subject_id = _parse_fhir_reference(resource_id, 'Patient')
            if subject_id is None:
                return _fhir_error(404, f'Patient {resource_id} not found')
            patient = get_fhir_patient(subject_id)
            if not patient:
                return _fhir_error(404, f'Patient {resource_id} not found')
            return _fhir_json(transformers.patient_to_fhir(patient))

        # Search
        gender = request.GET.get('gender')
        _id = request.GET.get('_id')
        subject_id = None
        if _id:
            subject_id = _parse_fhir_reference(_id, 'Patient')
        gender_code = None
        if gender:
            gender_code = 'M' if gender.lower() in ('male', 'm') else 'F'

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total, patients = get_fhir_patients(gender=gender_code, subject_id=subject_id, page=page)
        return _paginate_bundle(request, total, patients, transformers.patient_to_fhir)


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------

class EncounterView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            hadm_id = _parse_fhir_reference(resource_id, 'Encounter')
            if hadm_id is None:
                return _fhir_error(404, f'Encounter {resource_id} not found')
            enc = get_fhir_encounter(hadm_id)
            if not enc:
                return _fhir_error(404, f'Encounter {resource_id} not found')
            return _fhir_json(transformers.encounter_to_fhir(enc))

        patient_ref = request.GET.get('patient')
        patient_id = _parse_fhir_reference(patient_ref, 'Patient') if patient_ref else None
        date_filter = request.GET.get('date', '')

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total, encounters = get_fhir_encounters(
            patient_subject_id=patient_id,
            date_filter=date_filter or None,
            page=page,
        )
        return _paginate_bundle(request, total, encounters, transformers.encounter_to_fhir)


# ---------------------------------------------------------------------------
# Observation (Lab + Vitals)
# ---------------------------------------------------------------------------

class ObservationView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            rid = str(resource_id)
            if rid.startswith('mimic-lab-'):
                try:
                    lab_id = int(rid.replace('mimic-lab-', ''))
                    lab = get_fhir_lab(lab_id)
                    if lab:
                        return _fhir_json(transformers.lab_to_fhir(lab))
                except (ValueError, TypeError):
                    pass
            elif rid.startswith('mimic-vital-'):
                try:
                    vital_pk = int(rid.replace('mimic-vital-', ''))
                    vital = get_fhir_vital(vital_pk)
                    if vital:
                        return _fhir_json(transformers.vital_to_fhir(vital))
                except (ValueError, TypeError):
                    pass
            return _fhir_error(404, f'Observation {resource_id} not found')

        category = request.GET.get('category', '').lower()
        patient_ref = request.GET.get('patient')
        encounter_ref = request.GET.get('encounter')
        code = request.GET.get('code')
        date_param = request.GET.get('date', '')

        patient_id = _parse_fhir_reference(patient_ref, 'Patient') if patient_ref else None
        encounter_id = _parse_fhir_reference(encounter_ref, 'Encounter') if encounter_ref else None

        include_labs = category in ('', 'laboratory')
        include_vitals = category in ('', 'vital-signs')

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total_labs = 0
        total_vitals = 0
        lab_items = []
        vital_items = []

        if include_labs:
            total_labs, lab_items = get_fhir_labs(
                patient_subject_id=patient_id,
                encounter_hadm_id=encounter_id,
                code=code,
                date_filter=date_param or None,
                page=page,
            )

        if include_vitals:
            total_vitals, vital_items = get_fhir_vitals(
                patient_subject_id=patient_id,
                encounter_hadm_id=encounter_id,
                code=code,
                date_filter=date_param or None,
                page=page,
            )

        total = total_labs + total_vitals

        entries = []
        # Labs first, then vitals (matching original ordering)
        start = (page - 1) * PAGE_SIZE
        if start < total_labs:
            entries.extend(transformers.lab_to_fhir(l) for l in lab_items)
        remaining = PAGE_SIZE - len(entries)
        if remaining > 0 and include_vitals:
            entries.extend(transformers.vital_to_fhir(v) for v in vital_items[:remaining])

        base_url = request.build_absolute_uri(request.path)
        params = request.GET.copy()
        links = [{'relation': 'self', 'url': request.build_absolute_uri()}]
        if start + PAGE_SIZE < total:
            params['_page'] = str(page + 1)
            links.append({'relation': 'next', 'url': f'{base_url}?{params.urlencode()}'})
        if page > 1:
            params['_page'] = str(page - 1)
            links.append({'relation': 'previous', 'url': f'{base_url}?{params.urlencode()}'})

        return _fhir_json(transformers.make_bundle(entries, total=total, links=links))


# ---------------------------------------------------------------------------
# Condition
# ---------------------------------------------------------------------------

class ConditionView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            rid = str(resource_id)
            if rid.startswith('mimic-dx-'):
                parts = rid[9:].rsplit('-', 1)
                if len(parts) == 2:
                    try:
                        hadm_id, seq_num = int(parts[0]), int(parts[1])
                        dx = get_fhir_condition(hadm_id, seq_num)
                        if dx:
                            return _fhir_json(transformers.diagnosis_to_fhir(dx))
                    except (ValueError, TypeError):
                        pass
            return _fhir_error(404, f'Condition {resource_id} not found')

        patient_ref = request.GET.get('patient')
        encounter_ref = request.GET.get('encounter')
        code = request.GET.get('code')

        sid = _parse_fhir_reference(patient_ref, 'Patient') if patient_ref else None
        eid = _parse_fhir_reference(encounter_ref, 'Encounter') if encounter_ref else None

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total, items = get_fhir_conditions(
            patient_subject_id=sid, encounter_hadm_id=eid, code=code, page=page
        )
        return _paginate_bundle(request, total, items, transformers.diagnosis_to_fhir)


# ---------------------------------------------------------------------------
# Procedure
# ---------------------------------------------------------------------------

class ProcedureView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            rid = str(resource_id)
            if rid.startswith('mimic-proc-'):
                parts = rid[11:].rsplit('-', 1)
                if len(parts) == 2:
                    try:
                        hadm_id, seq_num = int(parts[0]), int(parts[1])
                        proc = get_fhir_procedure(hadm_id, seq_num)
                        if proc:
                            return _fhir_json(transformers.procedure_to_fhir(proc))
                    except (ValueError, TypeError):
                        pass
            return _fhir_error(404, f'Procedure {resource_id} not found')

        patient_ref = request.GET.get('patient')
        encounter_ref = request.GET.get('encounter')

        sid = _parse_fhir_reference(patient_ref, 'Patient') if patient_ref else None
        eid = _parse_fhir_reference(encounter_ref, 'Encounter') if encounter_ref else None

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total, items = get_fhir_procedures(
            patient_subject_id=sid, encounter_hadm_id=eid, page=page
        )
        return _paginate_bundle(request, total, items, transformers.procedure_to_fhir)


# ---------------------------------------------------------------------------
# MedicationRequest
# ---------------------------------------------------------------------------

class MedicationRequestView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            rid = str(resource_id)
            if rid.startswith('mimic-med-'):
                try:
                    pk = int(rid.replace('mimic-med-', ''))
                    med = get_fhir_medication(pk)
                    if med:
                        return _fhir_json(transformers.medication_to_fhir(med))
                except (ValueError, TypeError):
                    pass
            return _fhir_error(404, f'MedicationRequest {resource_id} not found')

        patient_ref = request.GET.get('patient')
        encounter_ref = request.GET.get('encounter')

        sid = _parse_fhir_reference(patient_ref, 'Patient') if patient_ref else None
        eid = _parse_fhir_reference(encounter_ref, 'Encounter') if encounter_ref else None

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total, items = get_fhir_medications(
            patient_subject_id=sid, encounter_hadm_id=eid, page=page
        )
        return _paginate_bundle(request, total, items, transformers.medication_to_fhir)


# ---------------------------------------------------------------------------
# DocumentReference
# ---------------------------------------------------------------------------

class DocumentReferenceView(FHIRView):
    def get(self, request, resource_id=None):
        if resource_id:
            rid = str(resource_id)
            if rid.startswith('mimic-note-'):
                note_id = rid.replace('mimic-note-', '')
                note = get_fhir_note(note_id)
                if note:
                    return _fhir_json(transformers.note_to_fhir(note))
            return _fhir_error(404, f'DocumentReference {resource_id} not found')

        patient_ref = request.GET.get('patient')
        encounter_ref = request.GET.get('encounter')
        note_type = request.GET.get('type')

        sid = _parse_fhir_reference(patient_ref, 'Patient') if patient_ref else None
        eid = _parse_fhir_reference(encounter_ref, 'Encounter') if encounter_ref else None

        try:
            page = max(1, int(request.GET.get('_page', 1)))
        except (ValueError, TypeError):
            page = 1

        total, items = get_fhir_notes(
            patient_subject_id=sid, encounter_hadm_id=eid,
            note_type=note_type, page=page
        )
        return _paginate_bundle(request, total, items, transformers.note_to_fhir)


# ---------------------------------------------------------------------------
# Patient/$everything
# ---------------------------------------------------------------------------

class PatientEverythingView(FHIRView):
    def get(self, request, resource_id):
        subject_id = _parse_fhir_reference(resource_id, 'Patient')
        if subject_id is None:
            return _fhir_error(404, f'Patient {resource_id} not found')

        result = get_fhir_patient_everything(subject_id)
        if result is None:
            return _fhir_error(404, f'Patient {resource_id} not found')

        entries = [transformers.patient_to_fhir(result['patient'])]
        for enc in result['encounters']:
            entries.append(transformers.encounter_to_fhir(enc))
        for lab in result['labs']:
            entries.append(transformers.lab_to_fhir(lab))
        for vital in result['vitals']:
            entries.append(transformers.vital_to_fhir(vital))
        for dx in result['diagnoses']:
            entries.append(transformers.diagnosis_to_fhir(dx))
        for proc in result['procedures']:
            entries.append(transformers.procedure_to_fhir(proc))
        for med in result['medications']:
            entries.append(transformers.medication_to_fhir(med))
        for note in result['notes']:
            entries.append(transformers.note_to_fhir(note))

        return _fhir_json(transformers.make_bundle(entries, total=len(entries)))
