from rest_framework import serializers
from ..models import DashboardPreference


class DashboardPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for dashboard preferences.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = DashboardPreference
        fields = [
            'id', 'user', 'user_email', 'company', 'company_name',
            'layout', 'widget_preferences', 'default_time_range',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'company_name', 'created_at', 'updated_at'] 