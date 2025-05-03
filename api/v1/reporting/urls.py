from django.urls import path, include

app_name = 'reporting'

urlpatterns = [
    path('', include('reporting.urls')),
] 