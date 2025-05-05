from django.urls import path, include
from api.v1.reporting.views.audit_report import AuditSummaryReportView, UserActivityReportView
# Import other report views here

app_name = 'reporting'

urlpatterns = [
    path('', include('reporting.urls', namespace='reports')),
    # Audit reports
    path('audit/summary/', AuditSummaryReportView.as_view(), name='audit-summary-report'),
    path('audit/user-activity/', UserActivityReportView.as_view(), name='user-activity-report'),
    
    # Other reports here
] 