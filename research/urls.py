from django.urls import path
from . import views

urlpatterns = [
    # Cohorts
    path('research/cohorts/', views.CohortListCreateView.as_view(), name='cohort-list-create'),
    path('research/cohorts/compare/', views.CohortCompareView.as_view(), name='cohort-compare'),
    path('research/cohorts/<int:pk>/', views.CohortDetailView.as_view(), name='cohort-detail'),
    path('research/cohorts/<int:pk>/execute/', views.CohortExecuteView.as_view(), name='cohort-execute'),
    path('research/cohorts/<int:pk>/stats/', views.CohortStatsView.as_view(), name='cohort-stats'),
    path('research/cohorts/<int:pk>/members/', views.CohortMembersView.as_view(), name='cohort-members'),

    # Saved Queries
    path('research/queries/', views.QueryListCreateView.as_view(), name='query-list-create'),
    path('research/queries/<int:pk>/', views.QueryDetailView.as_view(), name='query-detail'),
    path('research/queries/<int:pk>/run/', views.QueryRunView.as_view(), name='query-run'),

    # Search & Export
    path('research/search/', views.SearchView.as_view(), name='research-search'),
    path('research/export/', views.ExportView.as_view(), name='research-export'),
]
