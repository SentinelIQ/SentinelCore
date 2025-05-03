from django.urls import path
from .views import IncidentMarkdownReportView, IncidentPdfReportView

app_name = 'reporting'

urlpatterns = [
    path('incidents/<uuid:incident_id>/report/markdown/',
         IncidentMarkdownReportView.as_view(),
         name='incident-markdown-report'),
    path('incidents/<uuid:incident_id>/report/pdf/',
         IncidentPdfReportView.as_view(),
         name='incident-pdf-report'),
] 