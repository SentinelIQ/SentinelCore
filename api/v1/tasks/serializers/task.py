from rest_framework import serializers
from tasks.models import Task
from api.v1.tasks.enums import TaskStatusEnum, TaskPriorityEnum
from api.core.utils.enum_utils import enum_to_choices


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    status = serializers.ChoiceField(choices=enum_to_choices(TaskStatusEnum))
    priority = serializers.ChoiceField(choices=enum_to_choices(TaskPriorityEnum))
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display', 
            'priority', 'priority_display', 'due_date', 'completion_date',
            'incident', 'assigned_to', 'order', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completion_date', 'created_by', 'company'] 