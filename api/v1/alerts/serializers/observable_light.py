from rest_framework import serializers
from observables.models import Observable


class ObservableLightSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Observable model used in alert context
    """
    class Meta:
        model = Observable
        fields = ['id', 'type', 'value', 'is_ioc', 'tags']
        read_only_fields = fields 