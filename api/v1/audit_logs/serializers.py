"""
Serializers for the audit_logs module.

This module contains serializers for the audit logs API.
"""

from rest_framework import serializers
from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from typing import Optional, Dict, Any
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

User = get_user_model()


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the LogEntry model from django-auditlog.
    
    Adds additional fields and formatting to the LogEntry model.
    """
    # Fields from LogEntry
    id = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    object_id = serializers.SerializerMethodField()
    action = serializers.IntegerField(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    changes = serializers.JSONField(read_only=True)
    remote_addr = serializers.IPAddressField(read_only=True, allow_null=True)
    
    # Custom fields
    user_id = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    content_type_name = serializers.SerializerMethodField()
    entity_type = serializers.SerializerMethodField()
    entity_id = serializers.SerializerMethodField()
    entity_name = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    response_status = serializers.SerializerMethodField()
    
    # Additional data fields
    additional_data = serializers.JSONField(read_only=True)
    request_method = serializers.SerializerMethodField()
    request_path = serializers.SerializerMethodField()
    request_data = serializers.SerializerMethodField()
    
    class Meta:
        model = LogEntry
        fields = [
            'id', 'timestamp', 'object_id', 'action', 'action_display', 
            'changes', 'remote_addr', 'user_id', 'user_display', 
            'content_type_name', 'entity_type', 'entity_id', 'entity_name',
            'company_id', 'company_name', 'additional_data',
            'request_method', 'request_path', 'request_data', 'response_status'
        ]

    @extend_schema_field(OpenApiTypes.STR)
    def get_user_id(self, obj):
        """Get user ID."""
        if obj.actor:
            return str(obj.actor.pk)
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_user_display(self, obj):
        """Get a compatible representation of the user."""
        if obj.actor:
            if hasattr(obj.actor, 'get_full_name') and obj.actor.get_full_name():
                return obj.actor.get_full_name()
            return str(obj.actor)
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_action_name(self, obj):
        """Get the name of the action."""
        return obj.get_action_display()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_content_type_name(self, obj):
        """Get content type name."""
        if obj.content_type:
            return obj.content_type.model
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_entity_type(self, obj):
        """Get entity type from additional data or content type."""
        if obj.additional_data and 'entity_type' in obj.additional_data:
            return obj.additional_data.get('entity_type')
        elif obj.content_type:
            return obj.content_type.model
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_entity_id(self, obj):
        """Get entity ID from object_pk."""
        return obj.object_pk
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_entity_name(self, obj):
        """Get entity name."""
        # Try to use object representation
        if obj.object_repr:
            return obj.object_repr
        
        # If no object representation but we have an ID and content type
        if obj.object_pk and obj.content_type:
            try:
                model_class = obj.content_type.model_class()
                if model_class:
                    instance = model_class.objects.filter(pk=obj.object_pk).first()
                    if instance:
                        return str(instance)
            except Exception:
                pass
        
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_object_id(self, obj):
        """Get object ID."""
        return obj.object_pk
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_company_id(self, obj):
        """Get company ID from additional data."""
        if obj.additional_data and 'company_id' in obj.additional_data:
            return obj.additional_data.get('company_id')
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_company_name(self, obj):
        """Get company name from additional data."""
        if obj.additional_data and 'company_name' in obj.additional_data:
            return obj.additional_data.get('company_name')
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_request_method(self, obj):
        """Get the request method."""
        if obj.additional_data and 'request_method' in obj.additional_data:
            return obj.additional_data.get('request_method')
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_request_path(self, obj):
        """Get the request path."""
        if obj.additional_data and 'request_path' in obj.additional_data:
            return obj.additional_data.get('request_path')
        return None
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_request_data(self, obj):
        """Get the request data."""
        if obj.additional_data and 'request_data' in obj.additional_data:
            return obj.additional_data.get('request_data')
        return None
        
    @extend_schema_field(OpenApiTypes.ANY)
    def get_response_status(self, obj):
        """Get the response status."""
        if obj.additional_data and 'response_status' in obj.additional_data:
            return obj.additional_data.get('response_status')
        return None


class AuditLogListSerializer(AuditLogSerializer):
    """
    Simplified serializer for audit logs listing with reduced fields.
    """
    class Meta:
        model = LogEntry
        fields = [
            'id', 'timestamp', 'user_display', 'action_display',
            'entity_type', 'entity_id', 'entity_name', 'company_name',
            'response_status'
        ] 