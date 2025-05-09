"""
URL configuration for sentineliq project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


def trigger_error(request):
    """Endpoint to test Sentry error reporting."""
    division_by_zero = 1 / 0


urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls', namespace='api')),
    
    # Sentry debug endpoint
    path('sentry-debug/', trigger_error, name='sentry-debug'),
    
    # Redirect root to API documentation
    path('', RedirectView.as_view(url='/api/v1/docs/', permanent=False)),
]
