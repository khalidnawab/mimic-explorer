"""Research workbench API views (cohorts, saved queries, search, export)."""

import csv
import io
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.duckdb_queries import (
    execute_criteria, get_cohort_patient_data, get_export_data,
    get_patient_ids_for_subject_ids,
)
from core.duckdb_manager import get_connection

def _conn():
    """Return a new cursor for thread-safe concurrent access."""
    return get_connection().cursor()

from .models import SavedQuery, CohortDefinition, CohortMember
from .serializers import (
    SavedQuerySerializer,
    CohortDefinitionSerializer,
    CohortDefinitionListSerializer,
)


# --- Cohort CRUD ---

class CohortListCreateView(ListCreateAPIView):
    queryset = CohortDefinition.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CohortDefinitionListSerializer
        return CohortDefinitionSerializer


class CohortDetailView(RetrieveUpdateDestroyAPIView):
    queryset = CohortDefinition.objects.all()
    serializer_class = CohortDefinitionSerializer


class CohortExecuteView(APIView):
    """POST /api/research/cohorts/<pk>/execute/ — run criteria engine and populate members."""

    def post(self, request, pk):
        try:
            cohort = CohortDefinition.objects.get(pk=pk)
        except CohortDefinition.DoesNotExist:
            return Response({'error': 'Cohort not found'}, status=status.HTTP_404_NOT_FOUND)

        results = execute_criteria(cohort.criteria)

        # Clear existing members and repopulate
        cohort.members.all().delete()
        members = [
            CohortMember(
                cohort=cohort,
                patient_id=r['patient_id'],
                encounter_id=r['encounter_id'],
                group_label=r.get('group_label', ''),
            )
            for r in results
        ]
        CohortMember.objects.bulk_create(members)

        # Update counts
        cohort.patient_count = len(set(r['patient_id'] for r in results))
        cohort.encounter_count = len(results)
        cohort.save(update_fields=['patient_count', 'encounter_count'])

        # Build response for first 100 members
        member_data = []
        conn = _conn()
        for m in cohort.members.all()[:100]:
            # Resolve patient subject_id from DuckDB
            row = conn.execute(
                "SELECT subject_id FROM patient WHERE id = ?", [m.patient_id]
            ).fetchone()
            enc_row = None
            if m.encounter_id:
                enc_row = conn.execute(
                    "SELECT hadm_id FROM encounter WHERE id = ?", [m.encounter_id]
                ).fetchone()
            member_data.append({
                'id': m.id, 'cohort': m.cohort_id,
                'subject_id': row[0] if row else None,
                'hadm_id': enc_row[0] if enc_row else None,
                'group_label': m.group_label,
            })

        return Response({
            'patient_count': cohort.patient_count,
            'encounter_count': cohort.encounter_count,
            'members': member_data,
        })


def _cohort_stats(cohort):
    """Compute summary statistics for a cohort."""
    patient_ids = list(cohort.members.values_list('patient_id', flat=True).distinct())
    encounter_ids = list(
        cohort.members.exclude(encounter_id__isnull=True)
        .values_list('encounter_id', flat=True)
    )

    data = get_cohort_patient_data(patient_ids, encounter_ids)
    patients = data['patients']
    encounters = data['encounters']

    # Age stats
    ages = [p[3] for p in patients]
    avg_age = round(sum(ages) / len(ages), 1) if ages else None

    # Gender distribution
    gender_dist = {}
    for p in patients:
        g = p[2]
        gender_dist[g] = gender_dist.get(g, 0) + 1

    # Mortality
    mortality = sum(1 for e in encounters if e[5])
    total_enc = len(encounters)

    # Age buckets
    age_buckets = {}
    for label, lo, hi in [('18-30', 18, 30), ('31-45', 31, 45), ('46-60', 46, 60),
                           ('61-75', 61, 75), ('76-90', 76, 90), ('90+', 91, 200)]:
        age_buckets[label] = sum(1 for p in patients if lo <= p[3] <= hi)

    # Group label distribution (from SQLite)
    group_dist = {}
    for gl, cnt in (
        cohort.members.exclude(group_label='')
        .values_list('group_label')
        .annotate(count=__import__('django.db.models', fromlist=['Count']).Count('id'))
        .values_list('group_label', 'count')
    ):
        group_dist[gl] = cnt

    return {
        'name': cohort.name,
        'patient_count': len(patients),
        'encounter_count': total_enc,
        'avg_age': avg_age,
        'gender_distribution': gender_dist,
        'age_distribution': age_buckets,
        'mortality_rate': round(mortality / total_enc * 100, 1) if total_enc else 0,
        'mortality_count': mortality,
        'group_distribution': group_dist,
    }


class CohortStatsView(APIView):
    def get(self, request, pk):
        try:
            cohort = CohortDefinition.objects.get(pk=pk)
        except CohortDefinition.DoesNotExist:
            return Response({'error': 'Cohort not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_cohort_stats(cohort))


class CohortMembersView(APIView):
    def get(self, request, pk):
        try:
            cohort = CohortDefinition.objects.get(pk=pk)
        except CohortDefinition.DoesNotExist:
            return Response({'error': 'Cohort not found'}, status=status.HTTP_404_NOT_FOUND)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        search = request.query_params.get('search', '')
        group = request.query_params.get('group', '')

        members = cohort.members.all()
        if group:
            members = members.filter(group_label=group)

        total = members.count()
        start = (page - 1) * page_size
        members_page = list(members.order_by('patient_id')[start:start + page_size])

        # Resolve patient/encounter data from DuckDB
        conn = _conn()
        data = []
        for m in members_page:
            p_row = conn.execute(
                "SELECT subject_id, gender, anchor_age FROM patient WHERE id = ?",
                [m.patient_id]
            ).fetchone()
            if search and p_row and search not in str(p_row[0]):
                continue

            enc_row = None
            if m.encounter_id:
                enc_row = conn.execute(
                    "SELECT hadm_id, admittime, admission_type, hospital_expire_flag FROM encounter WHERE id = ?",
                    [m.encounter_id]
                ).fetchone()

            data.append({
                'subject_id': p_row[0] if p_row else None,
                'gender': p_row[1] if p_row else None,
                'anchor_age': p_row[2] if p_row else None,
                'group_label': m.group_label,
                'hadm_id': enc_row[0] if enc_row else None,
                'admittime': str(enc_row[1]) if enc_row and enc_row[1] else None,
                'admission_type': enc_row[2] if enc_row else None,
                'hospital_expire_flag': bool(enc_row[3]) if enc_row else None,
            })

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': data,
        })


class CohortCompareView(APIView):
    def post(self, request):
        cohort_a_id = request.data.get('cohort_a')
        cohort_b_id = request.data.get('cohort_b')

        if not cohort_a_id or not cohort_b_id:
            return Response({'error': 'cohort_a and cohort_b are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            cohort_a = CohortDefinition.objects.get(pk=cohort_a_id)
            cohort_b = CohortDefinition.objects.get(pk=cohort_b_id)
        except CohortDefinition.DoesNotExist:
            return Response({'error': 'Cohort not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'cohort_a': _cohort_stats(cohort_a),
            'cohort_b': _cohort_stats(cohort_b),
        })


# --- Saved Queries ---

class QueryListCreateView(ListCreateAPIView):
    queryset = SavedQuery.objects.all().order_by('-created_at')
    serializer_class = SavedQuerySerializer


class QueryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = SavedQuery.objects.all()
    serializer_class = SavedQuerySerializer


class QueryRunView(APIView):
    def post(self, request, pk):
        try:
            query = SavedQuery.objects.get(pk=pk)
        except SavedQuery.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)

        results = execute_criteria(query.query_definition)
        query.result_count = len(results)
        query.save(update_fields=['result_count'])

        conn = _conn()
        encounter_ids = [r['encounter_id'] for r in results if r.get('encounter_id')][:100]

        data = []
        for eid in encounter_ids:
            row = conn.execute("""
                SELECT e.hadm_id, p.subject_id, e.admittime, e.dischtime, e.admission_type
                FROM encounter e JOIN patient p ON e.patient_id = p.id
                WHERE e.id = ?
            """, [eid]).fetchone()
            if row:
                data.append({
                    'hadm_id': row[0], 'subject_id': row[1],
                    'admittime': str(row[2]) if row[2] else None,
                    'dischtime': str(row[3]) if row[3] else None,
                    'admission_type': row[4],
                })

        return Response({
            'total_results': len(results),
            'encounters': data,
        })


# --- Search ---

class SearchView(APIView):
    def post(self, request):
        criteria = request.data.get('criteria', {})
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 50))

        results = execute_criteria(criteria)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        page_results = results[start:end]

        conn = _conn()
        data = []
        for r in page_results:
            enc_row = conn.execute("""
                SELECT e.hadm_id, p.subject_id, e.admittime, e.dischtime, e.admission_type
                FROM encounter e JOIN patient p ON e.patient_id = p.id
                WHERE e.id = ?
            """, [r['encounter_id']]).fetchone()
            if enc_row:
                dx_rows = conn.execute("""
                    SELECT icd_code, long_title FROM diagnosis
                    WHERE encounter_id = ? ORDER BY seq_num LIMIT 5
                """, [r['encounter_id']]).fetchall()
                data.append({
                    'patient_id': r['patient_id'],
                    'subject_id': enc_row[1],
                    'hadm_id': enc_row[0],
                    'admittime': str(enc_row[2]) if enc_row[2] else None,
                    'dischtime': str(enc_row[3]) if enc_row[3] else None,
                    'admission_type': enc_row[4],
                    'group_label': r.get('group_label', ''),
                    'diagnoses': [{'icd_code': d[0], 'title': d[1]} for d in dx_rows],
                })

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': data,
        })


# --- Export ---

class ExportView(APIView):
    def post(self, request):
        fmt = request.data.get('format', 'csv')
        cohort_id = request.data.get('cohort_id')
        patient_ids = request.data.get('patient_ids', [])
        data_types = request.data.get('data_types', [])

        if not data_types:
            return Response({'error': 'data_types is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Resolve patient set
        if cohort_id:
            try:
                cohort = CohortDefinition.objects.get(pk=cohort_id)
            except CohortDefinition.DoesNotExist:
                return Response({'error': 'Cohort not found'}, status=status.HTTP_404_NOT_FOUND)
            patient_pks = list(cohort.members.values_list('patient_id', flat=True).distinct())
        elif patient_ids:
            patient_pks = get_patient_ids_for_subject_ids(patient_ids)
        else:
            return Response({'error': 'cohort_id or patient_ids required'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not patient_pks:
            return Response({'error': 'No patients found'}, status=status.HTTP_404_NOT_FOUND)

        export_data = get_export_data(patient_pks, data_types)

        if fmt == 'json':
            return Response(export_data)

        # CSV streaming response
        def csv_rows():
            for dtype, rows in export_data.items():
                if not rows:
                    continue
                headers = list(rows[0].keys())
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([f'--- {dtype} ---'])
                writer.writerow(headers)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

                for row in rows:
                    writer.writerow([str(row.get(h, '')) for h in headers])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)

                writer.writerow([])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        response = StreamingHttpResponse(csv_rows(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mimic_export.csv"'
        return response
