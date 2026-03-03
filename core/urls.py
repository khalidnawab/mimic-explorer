from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.StatusView.as_view(), name='api-status'),
    path('import/browse-folder/', views.BrowseFolderView.as_view(), name='import-browse'),
    path('import/validate-folder/', views.ValidateFolderView.as_view(), name='import-validate'),
    path('import/start/', views.StartImportView.as_view(), name='import-start'),
    path('import/status/', views.ImportStatusView.as_view(), name='import-status'),
    path('import/cancel/', views.CancelImportView.as_view(), name='import-cancel'),
    path('import/supplement/', views.SupplementImportView.as_view(), name='import-supplement'),
    path('reset/', views.ResetView.as_view(), name='api-reset'),
]
