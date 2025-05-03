from rest_framework import serializers
from incidents.models import IncidentTask
from auth_app.models import User
from api.v1.incidents.enums import IncidentTaskStatusEnum
from api.core.utils.enum_utils import enum_to_choices


class AssigneeLightSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for User model when used as an assignee
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class IncidentTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for IncidentTask model
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assignee = AssigneeLightSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    status = serializers.ChoiceField(choices=enum_to_choices(IncidentTaskStatusEnum))
    
    class Meta:
        model = IncidentTask
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'priority', 'due_date', 'assignee', 'is_overdue',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def get_is_overdue(self, obj):
        """
        Check if the task is overdue
        """
        if obj.due_date and obj.status != IncidentTaskStatusEnum.COMPLETED.value:
            from django.utils import timezone
            return obj.due_date < timezone.now()
        return False


class IncidentTaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating incident tasks
    """
    assignee_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    
    status = serializers.ChoiceField(
        choices=enum_to_choices(IncidentTaskStatusEnum),
        default=IncidentTaskStatusEnum.PENDING.value
    )
    
    class Meta:
        model = IncidentTask
        fields = [
            'title', 'description', 'status', 'priority', 
            'due_date', 'assignee_id'
        ]
    
    def validate_assignee_id(self, value):
        """
        Validate the assignee exists and belongs to the same company
        """
        if not value:
            return None
            
        try:
            incident = self.context.get('incident')
            user = User.objects.get(id=value)
            
            # Check if user belongs to same company
            if incident and incident.company != user.company:
                raise serializers.ValidationError(
                    "Assignee must belong to the same company as the incident."
                )
                
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Specified user does not exist.")
    
    def create(self, validated_data):
        """
        Create a task with proper company and incident
        """
        incident = self.context.get('incident')
        request = self.context.get('request')
        
        # Get assignee from validated assignee_id
        assignee = validated_data.pop('assignee_id', None)
        
        # Create task instance
        task = IncidentTask(
            incident=incident,
            company=incident.company,
            created_by=request.user,
            assignee=assignee,
            **validated_data
        )
        task.save()
        
        return task


class IncidentTaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating incident tasks
    """
    assignee_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    
    status = serializers.ChoiceField(choices=enum_to_choices(IncidentTaskStatusEnum))
    
    class Meta:
        model = IncidentTask
        fields = [
            'title', 'description', 'status', 'priority',
            'due_date', 'assignee_id'
        ]
    
    def validate_assignee_id(self, value):
        """
        Validate the assignee exists and belongs to the same company
        """
        if not value:
            return None
            
        try:
            task = self.instance
            user = User.objects.get(id=value)
            
            # Check if user belongs to same company
            if task and task.company != user.company:
                raise serializers.ValidationError(
                    "Assignee must belong to the same company as the task."
                )
                
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Specified user does not exist.")
    
    def update(self, instance, validated_data):
        """
        Handle special case for assignee_id
        """
        # Handle assignee separately
        assignee = validated_data.pop('assignee_id', None)
        if assignee is not None:
            instance.assignee = assignee
        
        # Handle completed_at timestamp when status changes to completed
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Set completed_at if task is being marked as completed
        if old_status != IncidentTaskStatusEnum.COMPLETED.value and new_status == IncidentTaskStatusEnum.COMPLETED.value:
            from django.utils import timezone
            instance.completed_at = timezone.now()
        
        # Reset completed_at if task is being unmarked as completed
        if old_status == IncidentTaskStatusEnum.COMPLETED.value and new_status != IncidentTaskStatusEnum.COMPLETED.value:
            instance.completed_at = None
        
        # Update the remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance 