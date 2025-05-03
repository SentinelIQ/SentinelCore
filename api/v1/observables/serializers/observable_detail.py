from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .observable import ObservableSerializer


class ObservableDetailSerializer(ObservableSerializer):
    """
    Detailed serializer for full observable information.
    """
    execution_records = serializers.SerializerMethodField()
    elastic_data = serializers.SerializerMethodField()
    
    class Meta(ObservableSerializer.Meta):
        fields = ObservableSerializer.Meta.fields + [
            'execution_records',
            'elastic_data',
        ]
    
    @extend_schema_field(serializers.ListField())
    def get_execution_records(self, obj):
        """
        Return recent execution records for this observable.
        """
        records = obj.execution_records.all().order_by('-created_at')[:5]
        return [{
            'id': str(record.id),
            'module_name': record.module_name,
            'execution_type': record.execution_type,
            'status': record.status,
            'start_time': record.start_time,
            'end_time': record.end_time,
        } for record in records]
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_elastic_data(self, obj):
        """
        Return Elasticsearch data if available.
        """
        from observables.services.elastic import ElasticLookupService
        
        try:
            lookup_service = ElasticLookupService(company_id=obj.company.id)
            return lookup_service.find_by_type_and_value(obj.type, obj.value)
        except Exception:
            return None 