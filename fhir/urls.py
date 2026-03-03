from django.urls import path

from . import views

urlpatterns = [
    path('fhir/metadata', views.CapabilityStatementView.as_view(), name='fhir-metadata'),

    path('fhir/Patient/', views.PatientView.as_view(), name='fhir-patient-search'),
    path('fhir/Patient/<str:resource_id>/', views.PatientView.as_view(), name='fhir-patient-read'),
    path('fhir/Patient/<str:resource_id>/$everything', views.PatientEverythingView.as_view(), name='fhir-patient-everything'),

    path('fhir/Encounter/', views.EncounterView.as_view(), name='fhir-encounter-search'),
    path('fhir/Encounter/<str:resource_id>/', views.EncounterView.as_view(), name='fhir-encounter-read'),

    path('fhir/Observation/', views.ObservationView.as_view(), name='fhir-observation-search'),
    path('fhir/Observation/<str:resource_id>/', views.ObservationView.as_view(), name='fhir-observation-read'),

    path('fhir/Condition/', views.ConditionView.as_view(), name='fhir-condition-search'),
    path('fhir/Condition/<str:resource_id>/', views.ConditionView.as_view(), name='fhir-condition-read'),

    path('fhir/Procedure/', views.ProcedureView.as_view(), name='fhir-procedure-search'),
    path('fhir/Procedure/<str:resource_id>/', views.ProcedureView.as_view(), name='fhir-procedure-read'),

    path('fhir/MedicationRequest/', views.MedicationRequestView.as_view(), name='fhir-medicationrequest-search'),
    path('fhir/MedicationRequest/<str:resource_id>/', views.MedicationRequestView.as_view(), name='fhir-medicationrequest-read'),

    path('fhir/DocumentReference/', views.DocumentReferenceView.as_view(), name='fhir-documentreference-search'),
    path('fhir/DocumentReference/<str:resource_id>/', views.DocumentReferenceView.as_view(), name='fhir-documentreference-read'),
]
