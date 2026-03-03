"""Clinical data API views — backed by DuckDB."""

from rest_framework.response import Response
from rest_framework.views import APIView

from core.duckdb_queries import (
    get_labs_list, get_vitals_list, get_diagnoses_list, get_procedures_list,
    get_medications_list, get_notes_list, get_lab_items, get_vital_items,
)

PAGE_SIZE = 50


def _page_params(request):
    try:
        page = int(request.query_params.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    return page, PAGE_SIZE


class LabEventListView(APIView):
    def get(self, request):
        page, page_size = _page_params(request)
        abnormal = request.query_params.get('abnormal_only', '').lower() == 'true'
        data = get_labs_list(
            patient_subject_id=request.query_params.get('patient'),
            encounter_id=None,
            label=request.query_params.get('label'),
            itemid=request.query_params.get('itemid'),
            date_from=request.query_params.get('date_from'),
            date_to=request.query_params.get('date_to'),
            abnormal_only=abnormal,
            page=page, page_size=page_size,
        )
        # Resolve encounter filter by hadm_id
        encounter = request.query_params.get('encounter')
        if encounter:
            from core.duckdb_queries import _resolve_hadm_to_encounter_id
            enc_id = _resolve_hadm_to_encounter_id(int(encounter))
            data = get_labs_list(encounter_id=enc_id, label=request.query_params.get('label'),
                                itemid=request.query_params.get('itemid'),
                                date_from=request.query_params.get('date_from'),
                                date_to=request.query_params.get('date_to'),
                                abnormal_only=abnormal, page=page, page_size=page_size)
        return Response(data)


class VitalSignListView(APIView):
    def get(self, request):
        page, page_size = _page_params(request)
        encounter = request.query_params.get('encounter')
        enc_id = None
        if encounter:
            from core.duckdb_queries import _resolve_hadm_to_encounter_id
            enc_id = _resolve_hadm_to_encounter_id(int(encounter))
        data = get_vitals_list(
            patient_subject_id=request.query_params.get('patient'),
            encounter_id=enc_id,
            label=request.query_params.get('label'),
            itemid=request.query_params.get('itemid'),
            date_from=request.query_params.get('date_from'),
            date_to=request.query_params.get('date_to'),
            page=page, page_size=page_size,
        )
        return Response(data)


class DiagnosisListView(APIView):
    def get(self, request):
        page, page_size = _page_params(request)
        encounter = request.query_params.get('encounter')
        enc_id = None
        if encounter:
            from core.duckdb_queries import _resolve_hadm_to_encounter_id
            enc_id = _resolve_hadm_to_encounter_id(int(encounter))
        data = get_diagnoses_list(
            patient_subject_id=request.query_params.get('patient'),
            encounter_id=enc_id,
            icd_code=request.query_params.get('icd_code'),
            search=request.query_params.get('search'),
            page=page, page_size=page_size,
        )
        return Response(data)


class ProcedureListView(APIView):
    def get(self, request):
        page, page_size = _page_params(request)
        encounter = request.query_params.get('encounter')
        enc_id = None
        if encounter:
            from core.duckdb_queries import _resolve_hadm_to_encounter_id
            enc_id = _resolve_hadm_to_encounter_id(int(encounter))
        data = get_procedures_list(
            patient_subject_id=request.query_params.get('patient'),
            encounter_id=enc_id,
            icd_code=request.query_params.get('icd_code'),
            search=request.query_params.get('search'),
            page=page, page_size=page_size,
        )
        return Response(data)


class MedicationListView(APIView):
    def get(self, request):
        page, page_size = _page_params(request)
        encounter = request.query_params.get('encounter')
        enc_id = None
        if encounter:
            from core.duckdb_queries import _resolve_hadm_to_encounter_id
            enc_id = _resolve_hadm_to_encounter_id(int(encounter))
        data = get_medications_list(
            patient_subject_id=request.query_params.get('patient'),
            encounter_id=enc_id,
            drug=request.query_params.get('drug'),
            date_from=request.query_params.get('date_from'),
            date_to=request.query_params.get('date_to'),
            page=page, page_size=page_size,
        )
        return Response(data)


class NoteListView(APIView):
    def get(self, request):
        page, page_size = _page_params(request)
        encounter = request.query_params.get('encounter')
        enc_id = None
        if encounter:
            from core.duckdb_queries import _resolve_hadm_to_encounter_id
            enc_id = _resolve_hadm_to_encounter_id(int(encounter))
        data = get_notes_list(
            patient_subject_id=request.query_params.get('patient'),
            encounter_id=enc_id,
            note_type=request.query_params.get('note_type'),
            page=page, page_size=page_size,
        )
        return Response(data)


class LabItemsView(APIView):
    def get(self, request):
        return Response(get_lab_items())


class VitalItemsView(APIView):
    def get(self, request):
        return Response(get_vital_items())
