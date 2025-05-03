from rest_framework import serializers
from sentinelvision.analyzers.virustotal import VirusTotalAnalyzer


class VirusTotalAnalyzerSerializer(serializers.ModelSerializer):
    """
    Serializer for VirusTotal analyzers.
    """
    class Meta:
        model = VirusTotalAnalyzer
        fields = [
            'id',
            'name',
            'module_type',
            'description',
            'use_premium_api',
            'request_rate_limit',
            'company',
            'is_active',
            'created_at',
            'updated_at',
        ]


class VirusTotalAnalyzerDetailSerializer(VirusTotalAnalyzerSerializer):
    """
    Detailed serializer for VirusTotal analyzers.
    """
    class Meta(VirusTotalAnalyzerSerializer.Meta):
        fields = VirusTotalAnalyzerSerializer.Meta.fields + [
            'configuration',
            'supported_observable_types',
            'tags',
        ]


class VirusTotalAnalyzerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating VirusTotal analyzers.
    """
    class Meta:
        model = VirusTotalAnalyzer
        fields = [
            'name',
            'description',
            'api_key',
            'use_premium_api',
            'request_rate_limit',
            'company',
            'supported_observable_types',
            'tags',
            'is_active',
        ]
        
    def validate_supported_observable_types(self, value):
        """
        Validate that the analyzer only supports compatible observable types.
        """
        valid_types = ['ip', 'domain', 'url', 'hash_md5', 'hash_sha1', 'hash_sha256']
        for obs_type in value:
            if obs_type not in valid_types:
                raise serializers.ValidationError(
                    f"VirusTotal does not support observable type '{obs_type}'"
                )
        return value 