from django.urls import path, include
from api.v1.reporting.views.audit_report import AuditSummaryReportView, UserActivityReportView
# Importar outras views de relatório aqui

app_name = 'reporting'

urlpatterns = [
    path('', include('reporting.urls')),
    # Relatórios de auditoria
    path('audit/summary/', AuditSummaryReportView.as_view(), name='audit-summary-report'),
    path('audit/user-activity/', UserActivityReportView.as_view(), name='user-activity-report'),
    
    # Outros relatórios aqui
] 