from rest_framework import serializers


class SystemConfigSerializer(serializers.Serializer):
    import_status = serializers.CharField()
    import_progress = serializers.JSONField()
    imported_modules = serializers.JSONField()
    total_patients = serializers.IntegerField()
    total_encounters = serializers.IntegerField()
    import_started_at = serializers.DateTimeField()
    import_completed_at = serializers.DateTimeField()
    mimic_version = serializers.CharField()
    mimic_data_path = serializers.CharField()


class FolderValidationSerializer(serializers.Serializer):
    folder_path = serializers.CharField()


class ImportStartSerializer(serializers.Serializer):
    folder_path = serializers.CharField()
    modules = serializers.ListField(child=serializers.CharField(), default=['hosp'])
    patient_limit = serializers.IntegerField(required=False, allow_null=True, default=None)
    generate_fhir = serializers.BooleanField(default=False)
    existing_patients_only = serializers.BooleanField(default=False)
