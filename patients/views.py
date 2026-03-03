"""Patient and encounter API views — backed by DuckDB."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.duckdb_queries import (
    get_patient_list, get_patient_detail, get_patient_timeline,
    get_encounter_list, get_encounter_detail,
    get_encounter_labs, get_encounter_vitals, get_encounter_diagnoses,
    get_encounter_procedures, get_encounter_medications, get_encounter_notes,
    get_encounter_icu_stays,
)

PAGE_SIZE = 50


def _page_params(request):
    """Extract page/page_size from DRF-style pagination."""
    try:
        page = int(request.query_params.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    return page, PAGE_SIZE


class PatientListView(APIView):
    """Searchable, filterable patient list."""

    def get(self, request):
        page, page_size = _page_params(request)
        data = get_patient_list(
            search=request.query_params.get('search'),
            gender=request.query_params.get('gender'),
            age_min=request.query_params.get('age_min'),
            age_max=request.query_params.get('age_max'),
            page=page,
            page_size=page_size,
        )
        return Response(data)


class PatientDetailView(APIView):
    """Single patient with encounter summary."""

    def get(self, request, subject_id):
        data = get_patient_detail(subject_id)
        if data is None:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data)


class PatientTimelineView(APIView):
    """GET /api/patients/<subject_id>/timeline/ - All events chronologically."""

    def get(self, request, subject_id):
        events = get_patient_timeline(subject_id)
        if events is None:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(events)


class EncounterListView(APIView):
    """Filterable encounter list."""

    def get(self, request):
        page, page_size = _page_params(request)
        data = get_encounter_list(
            patient=request.query_params.get('patient'),
            admission_type=request.query_params.get('admission_type'),
            date_from=request.query_params.get('date_from'),
            date_to=request.query_params.get('date_to'),
            page=page,
            page_size=page_size,
        )
        return Response(data)


class EncounterDetailView(APIView):
    """Single encounter with full clinical context."""

    def get(self, request, hadm_id):
        data = get_encounter_detail(hadm_id)
        if data is None:
            return Response({'error': 'Encounter not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data)


class EncounterLabsView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_labs(hadm_id, page=page, page_size=page_size))


class EncounterVitalsView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_vitals(hadm_id, page=page, page_size=page_size))


class EncounterDiagnosesView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_diagnoses(hadm_id, page=page, page_size=page_size))


class EncounterProceduresView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_procedures(hadm_id, page=page, page_size=page_size))


class EncounterMedicationsView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_medications(hadm_id, page=page, page_size=page_size))


class EncounterNotesView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_notes(hadm_id, page=page, page_size=page_size))


class EncounterICUStaysView(APIView):
    def get(self, request, hadm_id):
        page, page_size = _page_params(request)
        return Response(get_encounter_icu_stays(hadm_id, page=page, page_size=page_size))
