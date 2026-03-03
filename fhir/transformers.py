"""FHIR R4 resource transformers.

Pure functions converting Django model instances to FHIR R4 JSON dicts.
No fhir.resources validation at serve time for performance.
"""

import base64
from datetime import date


def _isoformat(dt):
    """Format a datetime/date to ISO string, or None."""
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)


def patient_to_fhir(patient) -> dict:
    """Convert Patient model to FHIR Patient resource."""
    birth_year = patient.anchor_year - patient.anchor_age
    resource = {
        'resourceType': 'Patient',
        'id': f'mimic-{patient.subject_id}',
        'identifier': [{
            'system': 'http://mimic.mit.edu/fhir/identifier/patient',
            'value': str(patient.subject_id),
        }],
        'gender': 'male' if patient.gender == 'M' else 'female',
        'birthDate': f'{birth_year}-01-01',
    }
    if patient.dod:
        resource['deceasedDateTime'] = _isoformat(patient.dod)
    return resource


def encounter_to_fhir(encounter) -> dict:
    """Convert Encounter model to FHIR Encounter resource."""
    admission_type = encounter.admission_type.upper() if encounter.admission_type else ''
    if 'EMERGENCY' in admission_type or 'URGENT' in admission_type:
        act_code = 'EMER'
    elif 'ELECTIVE' in admission_type or 'SURGICAL' in admission_type:
        act_code = 'AMB'
    else:
        act_code = 'IMP'

    resource = {
        'resourceType': 'Encounter',
        'id': f'mimic-{encounter.hadm_id}',
        'status': 'finished',
        'class': {
            'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
            'code': act_code,
        },
        'subject': {'reference': f'Patient/mimic-{encounter.patient.subject_id}'},
        'period': {
            'start': _isoformat(encounter.admittime),
        },
    }
    if encounter.dischtime:
        resource['period']['end'] = _isoformat(encounter.dischtime)
    hospitalization = {}
    if encounter.admission_location:
        hospitalization['admitSource'] = {'text': encounter.admission_location}
    if encounter.discharge_location:
        hospitalization['dischargeDisposition'] = {'text': encounter.discharge_location}
    if hospitalization:
        resource['hospitalization'] = hospitalization
    return resource


def lab_to_fhir(lab) -> dict:
    """Convert LabEvent model to FHIR Observation (laboratory)."""
    resource = {
        'resourceType': 'Observation',
        'id': f'mimic-lab-{lab.labevent_id}',
        'status': 'final',
        'category': [{
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                'code': 'laboratory',
                'display': 'Laboratory',
            }],
        }],
        'code': {'text': lab.label},
        'subject': {'reference': f'Patient/mimic-{lab.patient.subject_id}'},
        'effectiveDateTime': _isoformat(lab.charttime),
    }
    if lab.encounter_id:
        resource['encounter'] = {'reference': f'Encounter/mimic-{lab.encounter.hadm_id}'}
    if lab.valuenum is not None:
        resource['valueQuantity'] = {
            'value': lab.valuenum,
            'unit': lab.valueuom or '',
        }
    elif lab.value:
        resource['valueString'] = lab.value
    ref_range = {}
    if lab.ref_range_lower is not None:
        ref_range['low'] = {'value': lab.ref_range_lower}
    if lab.ref_range_upper is not None:
        ref_range['high'] = {'value': lab.ref_range_upper}
    if ref_range:
        resource['referenceRange'] = [ref_range]
    if lab.flag:
        resource['interpretation'] = [{'text': lab.flag}]
    return resource


def vital_to_fhir(vital) -> dict:
    """Convert VitalSign model to FHIR Observation (vital-signs)."""
    resource = {
        'resourceType': 'Observation',
        'id': f'mimic-vital-{vital.pk}',
        'status': 'final',
        'category': [{
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                'code': 'vital-signs',
                'display': 'Vital Signs',
            }],
        }],
        'code': {'text': vital.label},
        'subject': {'reference': f'Patient/mimic-{vital.patient.subject_id}'},
        'effectiveDateTime': _isoformat(vital.charttime),
    }
    if vital.encounter_id:
        resource['encounter'] = {'reference': f'Encounter/mimic-{vital.encounter.hadm_id}'}
    if vital.valuenum is not None:
        resource['valueQuantity'] = {
            'value': vital.valuenum,
            'unit': vital.valueuom or '',
        }
    elif vital.value:
        resource['valueString'] = vital.value
    return resource


def diagnosis_to_fhir(dx) -> dict:
    """Convert Diagnosis model to FHIR Condition resource."""
    if dx.icd_version == 10:
        system = 'http://hl7.org/fhir/sid/icd-10-cm'
    else:
        system = 'http://hl7.org/fhir/sid/icd-9-cm'

    return {
        'resourceType': 'Condition',
        'id': f'mimic-dx-{dx.encounter.hadm_id}-{dx.seq_num}',
        'subject': {'reference': f'Patient/mimic-{dx.patient.subject_id}'},
        'encounter': {'reference': f'Encounter/mimic-{dx.encounter.hadm_id}'},
        'code': {
            'coding': [{
                'system': system,
                'code': dx.icd_code,
                'display': dx.long_title,
            }],
            'text': dx.long_title,
        },
    }


def procedure_to_fhir(proc) -> dict:
    """Convert Procedure model to FHIR Procedure resource."""
    if proc.icd_version == 10:
        system = 'http://hl7.org/fhir/sid/icd-10-pcs'
    else:
        system = 'http://hl7.org/fhir/sid/icd-9-cm'

    return {
        'resourceType': 'Procedure',
        'id': f'mimic-proc-{proc.encounter.hadm_id}-{proc.seq_num}',
        'status': 'completed',
        'subject': {'reference': f'Patient/mimic-{proc.patient.subject_id}'},
        'encounter': {'reference': f'Encounter/mimic-{proc.encounter.hadm_id}'},
        'code': {
            'coding': [{
                'system': system,
                'code': proc.icd_code,
                'display': proc.long_title,
            }],
            'text': proc.long_title,
        },
    }


def medication_to_fhir(med) -> dict:
    """Convert Medication model to FHIR MedicationRequest resource."""
    resource = {
        'resourceType': 'MedicationRequest',
        'id': f'mimic-med-{med.pk}',
        'status': 'completed',
        'intent': 'order',
        'medicationCodeableConcept': {
            'text': med.drug,
        },
        'subject': {'reference': f'Patient/mimic-{med.patient.subject_id}'},
        'encounter': {'reference': f'Encounter/mimic-{med.encounter.hadm_id}'},
    }
    if med.ndc:
        resource['medicationCodeableConcept']['coding'] = [{
            'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'code': med.ndc,
        }]
    dosage = {}
    if med.dose_val_rx or med.dose_unit_rx:
        dose_quantity = {}
        if med.dose_val_rx:
            try:
                dose_quantity['value'] = float(med.dose_val_rx)
            except (ValueError, TypeError):
                dose_quantity['value'] = med.dose_val_rx
        if med.dose_unit_rx:
            dose_quantity['unit'] = med.dose_unit_rx
        if dose_quantity:
            dosage['doseAndRate'] = [{'doseQuantity': dose_quantity}]
    if med.route:
        dosage['route'] = {'text': med.route}
    if dosage:
        resource['dosageInstruction'] = [dosage]
    return resource


def note_to_fhir(note) -> dict:
    """Convert Note model to FHIR DocumentReference with base64 content."""
    encoded_text = base64.b64encode(note.text.encode('utf-8')).decode('ascii')
    resource = {
        'resourceType': 'DocumentReference',
        'id': f'mimic-note-{note.note_id}',
        'status': 'current',
        'type': {'text': note.note_type},
        'subject': {'reference': f'Patient/mimic-{note.patient.subject_id}'},
        'content': [{
            'attachment': {
                'contentType': 'text/plain',
                'data': encoded_text,
            },
        }],
    }
    if note.encounter_id:
        resource['context'] = {
            'encounter': [{'reference': f'Encounter/mimic-{note.encounter.hadm_id}'}],
        }
    if note.charttime:
        resource['date'] = _isoformat(note.charttime)
    return resource


def make_bundle(entries, bundle_type='searchset', total=None, links=None) -> dict:
    """Wrap a list of FHIR resources into a Bundle."""
    bundle = {
        'resourceType': 'Bundle',
        'type': bundle_type,
        'entry': [{'resource': e, 'fullUrl': f"{e['resourceType']}/{e['id']}"} for e in entries],
    }
    if total is not None:
        bundle['total'] = total
    if links:
        bundle['link'] = links
    return bundle
