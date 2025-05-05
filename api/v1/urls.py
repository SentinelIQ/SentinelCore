from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

app_name = 'v1'

# URLs with kebab-case and category prefixes
urlpatterns = [
    # Auth endpoints
    path('auth/', include('api.v1.auth.urls', namespace='auth')),
    
    # Companies endpoints
    path('companies/', include('api.v1.companies.urls', namespace='companies')),
    
    # Common endpoints
    path('common/', include('api.v1.common.urls', namespace='common')),
    
    # Alerts endpoints
    path('alerts/', include('api.v1.alerts.urls', namespace='alerts')),
    
    # Incidents endpoints
    path('incidents/', include('api.v1.incidents.urls', namespace='incidents')),
    
    # Observables endpoints
    path('observables/', include('api.v1.observables.urls', namespace='observables')),
    
    # Tasks endpoints
    path('tasks/', include('api.v1.tasks.urls', namespace='tasks')),
    
    # Reporting endpoints
    path('reporting/', include('api.v1.reporting.urls', namespace='reporting')),
    
    # Wiki endpoints
    path('wiki/', include('api.v1.wiki.urls', namespace='wiki')),
    
    # Notifications endpoints
    path('notifications/', include('api.v1.notifications.urls', namespace='notifications')),
    
    # Dashboard endpoints
    path('dashboard/', include('api.v1.dashboard.urls', namespace='dashboard')),
    
    # SentinelVision endpoints
    path('sentinel-vision/', include('api.v1.sentinelvision.urls', namespace='sentinelvision')),
    
    # MITRE ATT&CK endpoints
    path('mitre/', include('api.v1.mitre.urls', namespace='mitre')),
    
    # Audit logs endpoints
    path('audit-logs/', include('api.v1.audit_logs.urls', namespace='audit_logs')),
    
    # OpenAPI Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='v1:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='v1:schema'), name='redoc'),
] 