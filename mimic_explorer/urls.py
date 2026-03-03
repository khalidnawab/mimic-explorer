from django.urls import path, include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    # API routes
    path('api/', include('core.urls')),
    path('api/', include('patients.urls')),
    path('api/', include('clinical.urls')),
    path('api/', include('dashboards.urls')),
    path('api/', include('research.urls')),

    # FHIR endpoints at root (not under /api/)
    path('', include('fhir.urls')),

    # Catch-all: serve the React SPA
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='spa'),
]
