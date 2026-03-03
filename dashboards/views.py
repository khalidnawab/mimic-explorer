"""Dashboard aggregation API views — backed by DuckDB."""

from rest_framework.views import APIView
from rest_framework.response import Response

from core.duckdb_queries import get_demographics, get_utilization, get_clinical, get_missingness


class DemographicsView(APIView):
    def get(self, request):
        return Response(get_demographics())


class UtilizationView(APIView):
    def get(self, request):
        return Response(get_utilization())


class ClinicalView(APIView):
    def get(self, request):
        return Response(get_clinical())


class MissingnessView(APIView):
    def get(self, request):
        return Response(get_missingness())
