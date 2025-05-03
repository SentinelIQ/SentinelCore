from rest_framework import serializers
from sentinelvision.responders.block_ip import BlockIPResponder


class BlockIPResponderSerializer(serializers.ModelSerializer):
    """
    Serializer for Block IP responders.
    """
    class Meta:
        model = BlockIPResponder
        fields = [
            'id',
            'name',
            'module_type',
            'description',
            'integration_type',
            'api_url',
            'verify_ssl',
            'company',
            'is_active',
            'created_at',
            'updated_at',
        ]


class BlockIPResponderDetailSerializer(BlockIPResponderSerializer):
    """
    Detailed serializer for Block IP responders.
    """
    class Meta(BlockIPResponderSerializer.Meta):
        fields = BlockIPResponderSerializer.Meta.fields + [
            'configuration',
            'supported_observable_types',
            'additional_params',
            'tags',
        ]


class BlockIPResponderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Block IP responders.
    """
    class Meta:
        model = BlockIPResponder
        fields = [
            'name',
            'description',
            'integration_type',
            'api_url',
            'api_key',
            'verify_ssl',
            'additional_params',
            'company',
            'supported_observable_types',
            'tags',
            'is_active',
        ]
        
    def validate_supported_observable_types(self, value):
        """
        Validate that the responder only supports IP observable type.
        """
        if len(value) != 1 or 'ip' not in value:
            raise serializers.ValidationError(
                "BlockIPResponder only supports 'ip' observable type"
            )
        return value 