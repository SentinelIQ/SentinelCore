from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# URLs with kebab-case and category prefixes
urlpatterns = [
    # Auth endpoints
    path('auth/', include('api.v1.auth.urls')),
    
    # Companies endpoints
    path('companies/', include('api.v1.companies.urls')),
    
    # Common endpoints
    path('common/', include('api.v1.common.urls')),
    
    # Alerts endpoints
    path('alerts/', include('api.v1.alerts.urls')),
    
    # Incidents endpoints
    path('incidents/', include('api.v1.incidents.urls')),
    
    # Observables endpoints
    path('observables/', include('api.v1.observables.urls')),
    
    # Tasks endpoints
    path('tasks/', include('api.v1.tasks.urls')),
    
    # Reporting endpoints
    path('reporting/', include('api.v1.reporting.urls')),
    
    # Wiki endpoints
    path('wiki/', include('api.v1.wiki.urls')),
    
    # Notifications endpoints
    path('notifications/', include('api.v1.notifications.urls')),
    
    # Dashboard endpoints
    path('dashboard/', include('api.v1.dashboard.urls')),
    
    # SentinelVision endpoints
    path('sentinel-vision/', include('api.v1.sentinelvision.urls')),
    
    # MITRE ATT&CK endpoints
    path('mitre/', include('api.v1.mitre.urls')),
    
    # Audit logs endpoints
    path('audit-logs/', include('api.v1.audit_logs.urls')),
    
    # OpenAPI Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] 