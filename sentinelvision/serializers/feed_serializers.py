from rest_framework import serializers
from sentinelvision.models import FeedRegistry
from sentinelvision.feeds import get_feed_class


class FeedRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedRegistry
        fields = '__all__'
        read_only_fields = ('last_sync', 'next_sync', 'sync_status', 'total_iocs', 
                          'last_import_count', 'total_imports', 'error_count', 
                          'last_error', 'last_log', 'created_at', 'updated_at')


class FeedUpdateSerializer(serializers.Serializer):
    feed_type = serializers.CharField()
    company_id = serializers.UUIDField(required=False)
    
    def validate_feed_type(self, value):
        feed_class = get_feed_class(value)
        if not feed_class:
            raise serializers.ValidationError(f"Invalid feed type: {value}")
        return value


class GenericFeedSerializer(serializers.ModelSerializer):
    """
    Generic serializer for any feed type.
    """
    class Meta:
        fields = [
            'id',
            'name',
            'module_type',
            'description',
            'feed_type',
            'feed_url',
            'interval_hours',
            'last_run',
            'auto_mark_as_ioc',
            'company',
            'is_active',
            'created_at',
            'updated_at',
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.Meta.model = self.instance.__class__
        elif 'feed_type' in self.initial_data:
            feed_class = get_feed_class(self.initial_data['feed_type'])
            if feed_class:
                self.Meta.model = feed_class


class GenericFeedDetailSerializer(GenericFeedSerializer):
    """
    Detailed serializer for any feed type.
    """
    class Meta(GenericFeedSerializer.Meta):
        fields = GenericFeedSerializer.Meta.fields + [
            'configuration',
            'supported_observable_types',
            'tags',
        ] 