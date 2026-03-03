from rest_framework import serializers
from .models import SavedQuery, CohortDefinition, CohortMember


class SavedQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedQuery
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CohortDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortDefinition
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'patient_count', 'encounter_count']


class CohortDefinitionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortDefinition
        fields = ['id', 'name', 'patient_count', 'encounter_count', 'created_at']
