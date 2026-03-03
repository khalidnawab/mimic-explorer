import threading

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SystemConfig
from .serializers import SystemConfigSerializer, FolderValidationSerializer, ImportStartSerializer
from .importer import validate_mimic_folder, MIMICImporter

from research.models import CohortMember, CohortDefinition, SavedQuery

# Global reference to the import thread and cancel event
_import_thread = None
_cancel_event = threading.Event()


class StatusView(APIView):
    """GET /api/status/ - Returns current system configuration."""

    def get(self, request):
        config = SystemConfig.get_solo()
        serializer = SystemConfigSerializer(config)
        return Response(serializer.data)


class BrowseFolderView(APIView):
    """POST /api/import/browse-folder/ - Open native folder picker dialog."""

    def post(self, request):
        import threading

        result = {'path': ''}

        def pick_folder():
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                folder = filedialog.askdirectory(
                    title='Select MIMIC-IV Data Folder',
                )
                root.destroy()
                result['path'] = folder or ''
            except Exception:
                result['path'] = ''

        t = threading.Thread(target=pick_folder)
        t.start()
        t.join(timeout=120)

        return Response({'path': result['path']})


class ValidateFolderView(APIView):
    """POST /api/import/validate-folder/ - Validate MIMIC folder structure."""

    def post(self, request):
        serializer = FolderValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        folder_path = serializer.validated_data['folder_path']
        result = validate_mimic_folder(folder_path)
        return Response(result)


class StartImportView(APIView):
    """POST /api/import/start/ - Start data import in background thread."""

    def post(self, request):
        global _import_thread, _cancel_event

        if _import_thread and _import_thread.is_alive():
            return Response(
                {'error': 'An import is already in progress'},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ImportStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        folder_path = serializer.validated_data['folder_path']
        modules = serializer.validated_data['modules']
        patient_limit = serializer.validated_data.get('patient_limit')
        generate_fhir = serializer.validated_data.get('generate_fhir', False)
        existing_patients_only = serializer.validated_data.get('existing_patients_only', False)

        _cancel_event = threading.Event()

        importer = MIMICImporter(
            folder_path=folder_path,
            modules=modules,
            patient_limit=patient_limit,
            generate_fhir=generate_fhir,
            cancel_event=_cancel_event,
            existing_patients_only=existing_patients_only,
        )

        _import_thread = threading.Thread(target=importer.run, daemon=True)
        _import_thread.start()

        return Response({'status': 'started'}, status=status.HTTP_202_ACCEPTED)


class ImportStatusView(APIView):
    """GET /api/import/status/ - Poll import progress."""

    def get(self, request):
        config = SystemConfig.get_solo()
        return Response({
            'import_status': config.import_status,
            'import_progress': config.import_progress,
            'imported_modules': config.imported_modules,
            'total_patients': config.total_patients,
            'total_encounters': config.total_encounters,
            'import_started_at': config.import_started_at,
            'import_completed_at': config.import_completed_at,
        })


class CancelImportView(APIView):
    """POST /api/import/cancel/ - Cancel running import."""

    def post(self, request):
        global _cancel_event

        _cancel_event.set()
        return Response({'status': 'cancel_requested'})


class SupplementImportView(APIView):
    """POST /api/import/supplement/ - Import additional modules into existing data."""

    def post(self, request):
        global _import_thread, _cancel_event

        if _import_thread and _import_thread.is_alive():
            return Response(
                {'error': 'An import is already in progress'},
                status=status.HTTP_409_CONFLICT,
            )

        config = SystemConfig.get_solo()
        if config.import_status != 'completed':
            return Response(
                {'error': 'Initial import must be completed before supplementing'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ImportStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        folder_path = serializer.validated_data['folder_path']
        modules = serializer.validated_data['modules']
        patient_limit = serializer.validated_data.get('patient_limit')
        generate_fhir = serializer.validated_data.get('generate_fhir', False)
        existing_patients_only = serializer.validated_data.get('existing_patients_only', False)

        _cancel_event = threading.Event()

        importer = MIMICImporter(
            folder_path=folder_path,
            modules=modules,
            patient_limit=patient_limit,
            generate_fhir=generate_fhir,
            cancel_event=_cancel_event,
            existing_patients_only=existing_patients_only,
        )

        _import_thread = threading.Thread(target=importer.run, daemon=True)
        _import_thread.start()

        return Response({'status': 'started'}, status=status.HTTP_202_ACCEPTED)


class ResetView(APIView):
    """POST /api/reset/ - Wipe all imported data and reset to initial state."""

    def post(self, request):
        global _import_thread

        if _import_thread and _import_thread.is_alive():
            return Response(
                {'error': 'Cannot reset while an import is in progress'},
                status=status.HTTP_409_CONFLICT,
            )

        # Delete SQLite app-state data
        CohortMember.objects.all().delete()
        CohortDefinition.objects.all().delete()
        SavedQuery.objects.all().delete()

        # Reset DuckDB clinical data
        from core.duckdb_queries import reset_all_tables
        reset_all_tables()

        # Reset SystemConfig to defaults
        config = SystemConfig.get_solo()
        config.mimic_data_path = ''
        config.import_status = 'not_started'
        config.import_progress = {}
        config.imported_modules = []
        config.total_patients = 0
        config.total_encounters = 0
        config.import_started_at = None
        config.import_completed_at = None
        config.mimic_version = ''
        config.save()

        return Response({'status': 'reset_complete'})
