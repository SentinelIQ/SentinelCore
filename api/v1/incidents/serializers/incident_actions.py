from rest_framework import serializers
import uuid


class IncidentTimelineEntrySerializer(serializers.Serializer):
    """
    Serializer for adding timeline entries to incidents.
    """
    title = serializers.CharField(max_length=255)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    event_type = serializers.CharField(required=False, default='note')
    timestamp = serializers.DateTimeField(required=False)
    
    def validate_event_type(self, value):
        """
        Validate that event_type is one of the allowed types.
        """
        allowed_types = ['note', 'update', 'action', 'evidence', 'communication']
        if value not in allowed_types:
            raise serializers.ValidationError(f"Event type must be one of: {', '.join(allowed_types)}")
        return value


class IncidentAssignSerializer(serializers.Serializer):
    """
    Serializer for assigning incidents to users.
    """
    assignee = serializers.CharField()
    
    def validate_assignee(self, value):
        """
        Validate that the assignee exists and is active.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Try to convert to UUID if it's a string representation of UUID
        try:
            # Convert to UUID if it's a string
            uuid_value = uuid.UUID(str(value))
            
            # Try to find the user with the UUID
            try:
                user = User.objects.get(id=uuid_value)
                if not user.is_active:
                    raise serializers.ValidationError("User is inactive")
                return str(uuid_value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist")
                
        except (ValueError, TypeError):
            # If UUID conversion fails, try direct lookup
            try:
                user = User.objects.get(id=value)
                if not user.is_active:
                    raise serializers.ValidationError("User is inactive")
                return str(user.id)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Invalid user ID format") 