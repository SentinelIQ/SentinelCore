from rest_framework import serializers


class ObservableHistorySerializer(serializers.Serializer):
    """
    Serializer for observable history information.
    """
    timestamp = serializers.DateTimeField(read_only=True)
    source = serializers.CharField(read_only=True)
    action = serializers.CharField(read_only=True)
    user = serializers.CharField(read_only=True, allow_null=True)
    changes = serializers.DictField(read_only=True, allow_null=True)
    
    class Meta:
        fields = [
            'timestamp',
            'source',
            'action',
            'user',
            'changes',
        ] 