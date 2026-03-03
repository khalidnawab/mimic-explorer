from django.urls import path
from .views import DemographicsView, UtilizationView, ClinicalView, MissingnessView

urlpatterns = [
    path('dashboards/demographics/', DemographicsView.as_view(), name='dashboard-demographics'),
    path('dashboards/utilization/', UtilizationView.as_view(), name='dashboard-utilization'),
    path('dashboards/clinical/', ClinicalView.as_view(), name='dashboard-clinical'),
    path('dashboards/missingness/', MissingnessView.as_view(), name='dashboard-missingness'),
]
