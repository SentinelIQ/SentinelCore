from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from sentinelvision.models import ExecutionRecord
from observables.models import Observable


class ExecutionRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving execution records.
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = ExecutionRecord
        fields = [
            'id',
            'module_name',
            'module_type',
            'status',
            'started_at',
            'completed_at',
            'duration_seconds',
            'company',
            'company_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class ExecutionRecordDetailSerializer(ExecutionRecordSerializer):
    """
    Detailed serializer for execution records.
    """
    execution_arguments = serializers.JSONField(read_only=True)
    input_data = serializers.JSONField(read_only=True)
    output_data = serializers.JSONField(read_only=True)
    execution_log = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True)
    
    class Meta(ExecutionRecordSerializer.Meta):
        fields = ExecutionRecordSerializer.Meta.fields + [
            'execution_arguments',
            'input_data',
            'output_data',
            'execution_log',
            'error_message',
            'incident',
            'alert',
            'executed_by',
        ]
        read_only_fields = fields


class ExecutionRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating execution records.
    """
    class Meta:
        model = ExecutionRecord
        fields = [
            'module_name',
            'module_type',
            'company',
            'incident',
            'alert',
            'executed_by',
            'execution_arguments',
        ]
        
    def validate(self, data):
        """
        Validate that the related entities belong to the same company.
        """
        company = data.get('company')
        
        if company:
            # Validar que o incidente pertence à mesma empresa, se fornecido
            incident = data.get('incident')
            if incident and incident.company.id != company.id:
                raise serializers.ValidationError({
                    "incident": "O incidente deve pertencer à mesma empresa"
                })
                
            # Validar que o alerta pertence à mesma empresa, se fornecido
            alert = data.get('alert')
            if alert and alert.company.id != company.id:
                raise serializers.ValidationError({
                    "alert": "O alerta deve pertencer à mesma empresa"
                })
                
        return data 