from rest_framework import serializers
from alerts.models import Alert
from auth_app.models import User
from companies.models import Company
from api.v1.alerts.enums import AlertStatusEnum, AlertSeverityEnum, AlertTLPEnum, AlertPAPEnum
from .user_light import UserLightSerializer


class AlertSerializer(serializers.ModelSerializer):
    """
    Primary serializer for the Alert model.
    """
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tlp_display = serializers.CharField(source='get_tlp_display', read_only=True)
    pap_display = serializers.CharField(source='get_pap_display', read_only=True)
    
    created_by = UserLightSerializer(read_only=True)
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False
    )
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'description', 'severity', 'severity_display', 
            'source', 'source_ref', 'status', 'status_display', 'company', 
            'created_by', 'created_at', 'updated_at', 'tags', 'tlp', 'tlp_display',
            'pap', 'pap_display', 'date', 'artifact_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'artifact_count']
    
    def validate(self, attrs):
        """
        Validate that superusers without company provide a valid company.
        """
        request = self.context.get('request')
        if request and request.user.is_superuser and not request.user.company:
            company = attrs.get('company')
            if not company:
                raise serializers.ValidationError(
                    {"company": "Company is required when creating an alert as a superuser."}
                )
        
        # Check if updating to "escalated" status
        if getattr(self, 'instance', None) and 'status' in attrs and attrs['status'] == AlertStatusEnum.ESCALATED.value:
            # Check if the alert is already escalated
            if self.instance.status == AlertStatusEnum.ESCALATED.value:
                raise serializers.ValidationError({
                    "status": "This alert has already been escalated to an incident."
                })
        
        return attrs
    
    def create(self, validated_data):
        """Custom create method to handle any preprocessing before creating the alert."""
        # Ensure company object is properly processed when passed as string ID
        if 'company' in validated_data and isinstance(validated_data['company'], str):
            try:
                validated_data['company'] = Company.objects.get(id=validated_data['company'])
            except (Company.DoesNotExist, ValueError):
                raise serializers.ValidationError({"company": f"Invalid company ID: {validated_data['company']}"})
        
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        
        # Only override company if the user has one and none was provided
        if request.user.company and 'company' not in validated_data:
            validated_data['company'] = request.user.company
            
        return super().create(validated_data) 