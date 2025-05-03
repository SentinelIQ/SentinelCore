from rest_framework import serializers
from observables.models import Observable
from api.v1.observables.enums import ObservableTypeEnum, ObservableCategoryEnum, ObservableTLPEnum
from api.core.utils.enum_utils import enum_to_choices
from drf_spectacular.utils import extend_schema_field


class ObservableSerializer(serializers.ModelSerializer):
    """
    Serializer for Observable model.
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    tlp_display = serializers.CharField(source='get_tlp_display', read_only=True)
    
    type = serializers.ChoiceField(choices=enum_to_choices(ObservableTypeEnum))
    category = serializers.ChoiceField(
        choices=enum_to_choices(ObservableCategoryEnum),
        default=ObservableCategoryEnum.OTHER.value
    )
    tlp = serializers.ChoiceField(
        choices=enum_to_choices(ObservableTLPEnum),
        default=ObservableTLPEnum.AMBER.value
    )
    
    class Meta:
        model = Observable
        fields = [
            'id', 'type', 'type_display', 'value', 'description', 'category', 'category_display',
            'tags', 'tlp', 'tlp_display', 'alert', 'incident', 'enrichment_data', 
            'is_ioc', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'company'] 