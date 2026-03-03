from django.urls import path
from . import views

urlpatterns = [
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/<int:subject_id>/', views.PatientDetailView.as_view(), name='patient-detail'),
    path('patients/<int:subject_id>/timeline/', views.PatientTimelineView.as_view(), name='patient-timeline'),
    path('encounters/', views.EncounterListView.as_view(), name='encounter-list'),
    path('encounters/<int:hadm_id>/', views.EncounterDetailView.as_view(), name='encounter-detail'),
    path('encounters/<int:hadm_id>/labs/', views.EncounterLabsView.as_view(), name='encounter-labs'),
    path('encounters/<int:hadm_id>/vitals/', views.EncounterVitalsView.as_view(), name='encounter-vitals'),
    path('encounters/<int:hadm_id>/diagnoses/', views.EncounterDiagnosesView.as_view(), name='encounter-diagnoses'),
    path('encounters/<int:hadm_id>/procedures/', views.EncounterProceduresView.as_view(), name='encounter-procedures'),
    path('encounters/<int:hadm_id>/medications/', views.EncounterMedicationsView.as_view(), name='encounter-medications'),
    path('encounters/<int:hadm_id>/notes/', views.EncounterNotesView.as_view(), name='encounter-notes'),
    path('encounters/<int:hadm_id>/icu-stays/', views.EncounterICUStaysView.as_view(), name='encounter-icu-stays'),
]
