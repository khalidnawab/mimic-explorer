from django.urls import path
from . import views

urlpatterns = [
    path('labs/', views.LabEventListView.as_view(), name='lab-list'),
    path('vitals/', views.VitalSignListView.as_view(), name='vital-list'),
    path('diagnoses/', views.DiagnosisListView.as_view(), name='diagnosis-list'),
    path('procedures/', views.ProcedureListView.as_view(), name='procedure-list'),
    path('medications/', views.MedicationListView.as_view(), name='medication-list'),
    path('notes/', views.NoteListView.as_view(), name='note-list'),
    path('lab-items/', views.LabItemsView.as_view(), name='lab-items'),
    path('vital-items/', views.VitalItemsView.as_view(), name='vital-items'),
]
