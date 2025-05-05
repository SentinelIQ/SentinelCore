from rest_framework import serializers
from django.contrib.auth import get_user_model
from sentinelvision.models import (
    FeedModule, FeedExecutionRecord, 
    ExecutionSourceEnum, ExecutionStatusEnum,
    EnrichedIOC, IOCFeedMatch, IOCTypeEnum, EnrichmentStatusEnum,
    TLPLevelEnum
)
from drf_spectacular.utils import extend_schema_field

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Minimal user info for related fields."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = fields

class FeedModuleListSerializer(serializers.ModelSerializer):
    """Serializer for listing feed modules."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_global = serializers.SerializerMethodField()
    can_execute = serializers.SerializerMethodField()
    last_execution_status = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedModule
        fields = (
            'id', 'name', 'description', 'module_type', 'is_active',
            'company', 'company_name', 'is_global', 'can_execute',
            'last_run', 'last_error', 'error_count',
            'total_iocs_imported', 'total_processed', 'success_rate',
            'last_execution_status', 'cron_schedule'
        )
        read_only_fields = fields
    
    @extend_schema_field(serializers.BooleanField())
    def get_is_global(self, obj):
        """Check if feed is global (not linked to any company)."""
        return obj.company is None
    
    @extend_schema_field(serializers.BooleanField())
    def get_can_execute(self, obj):
        """Check if current user can execute this feed."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
            
        # Superusers can execute any feed
        if request.user.is_superuser:
            return True
            
        # For company-specific feeds, check if user belongs to that company
        if obj.company:
            return request.user.company == obj.company
            
        # For global feeds, only superusers can execute
        return False
    
    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_last_execution_status(self, obj):
        """Get status of the last execution."""
        last_execution = FeedExecutionRecord.objects.filter(
            feed=obj
        ).order_by('-started_at').first()
        
        if not last_execution:
            return None
            
        return {
            'id': str(last_execution.id),
            'status': last_execution.status,
            'started_at': last_execution.started_at.isoformat() if last_execution.started_at else None,
            'ended_at': last_execution.ended_at.isoformat() if last_execution.ended_at else None,
            'duration_seconds': last_execution.duration_seconds,
            'iocs_processed': last_execution.iocs_processed
        }

class FeedModuleSerializer(serializers.ModelSerializer):
    """Detailed serializer for feed modules."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_global = serializers.SerializerMethodField()
    can_execute = serializers.SerializerMethodField()
    feed_type = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedModule
        fields = (
            'id', 'name', 'description', 'module_type', 'is_active',
            'company', 'company_name', 'is_global', 'can_execute',
            'feed_url', 'interval_hours', 'auto_mark_as_ioc',
            'last_run', 'last_error', 'error_count',
            'last_successful_fetch', 'total_iocs_imported',
            'total_processed', 'success_rate', 'feed_type',
            'cron_schedule'
        )
        read_only_fields = (
            'id', 'module_type', 'total_processed', 'success_rate',
            'error_count', 'last_run', 'last_error', 'last_successful_fetch',
            'total_iocs_imported', 'feed_type'
        )
    
    @extend_schema_field(serializers.BooleanField())
    def get_is_global(self, obj):
        """Check if feed is global (not linked to any company)."""
        return obj.company is None
    
    @extend_schema_field(serializers.BooleanField())
    def get_can_execute(self, obj):
        """Check if current user can execute this feed."""
        request = self.context.get('request')
        if not request or not request.user:
            return False
            
        # Superusers can execute any feed
        if request.user.is_superuser:
            return True
            
        # For company-specific feeds, check if user belongs to that company
        if obj.company:
            return request.user.company == obj.company
            
        # For global feeds, only superusers can execute
        return False
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_feed_type(self, obj):
        """Get the specific feed type ID."""
        try:
            return getattr(obj, 'feed_id', None) or obj.__class__.__name__.lower()
        except:
            return None
    
    def validate_company(self, value):
        """
        Validate company field:
        - Only superusers can create/update global feeds
        - Regular users can only set their own company
        """
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
            
        # For create or full update
        if self.instance is None or value != self.instance.company:
            # If creating/updating as global feed (no company)
            if value is None:
                if not request.user.is_superuser:
                    raise serializers.ValidationError("Only superusers can create global feeds")
            else:
                # If setting specific company
                if not request.user.is_superuser and request.user.company != value:
                    raise serializers.ValidationError("You can only create feeds for your own company")
                
        return value

class FeedExecutionRecordSerializer(serializers.ModelSerializer):
    """Serializer for feed execution records."""
    feed_name = serializers.CharField(source='feed.name', read_only=True)
    executed_by = UserBasicSerializer(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    
    class Meta:
        model = FeedExecutionRecord
        fields = (
            'id', 'feed', 'feed_name', 'executed_by', 'source',
            'status', 'started_at', 'ended_at', 'duration_seconds',
            'log', 'iocs_processed', 'error_message'
        )
        read_only_fields = fields 

class IOCFeedMatchSerializer(serializers.ModelSerializer):
    """Serializer for IOC feed matches."""
    feed_name = serializers.CharField(source='feed.name', read_only=True)
    
    class Meta:
        model = IOCFeedMatch
        fields = (
            'id', 'feed', 'feed_name', 'match_time',
            'feed_confidence', 'feed_tags', 'metadata'
        )
        read_only_fields = fields

class EnrichedIOCSerializer(serializers.ModelSerializer):
    """Serializer for enriched IOCs."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    ioc_type_display = serializers.CharField(source='get_ioc_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    feed_matches = IOCFeedMatchSerializer(many=True, read_only=True)
    match_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EnrichedIOC
        fields = (
            'id', 'company', 'company_name', 'ioc_type', 'ioc_type_display',
            'value', 'status', 'status_display', 'first_seen', 'last_checked',
            'last_matched', 'source', 'description', 'tlp', 'confidence',
            'tags', 'feed_matches', 'match_count', 'es_index', 'es_doc_id'
        )
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField())
    def get_match_count(self, obj):
        """Count of feed matches for this IOC."""
        return obj.feed_matches.count()

class EnrichObservableRequestSerializer(serializers.Serializer):
    """Serializer for observable enrichment requests."""
    ioc_type = serializers.ChoiceField(
        choices=IOCTypeEnum.choices,
        help_text='Type of IOC (ip, domain, hash, etc.)'
    )
    ioc_value = serializers.CharField(
        max_length=1000,
        help_text='Value of the IOC to enrich'
    )
    description = serializers.CharField(
        max_length=1000,
        required=False,
        help_text='Optional description of the IOC'
    )
    
    def validate_ioc_value(self, value):
        """Validate IOC value is not empty."""
        if not value or value.strip() == '':
            raise serializers.ValidationError("IOC value cannot be empty")
        return value 