from rest_framework import serializers
from companies.models import Company
from drf_spectacular.utils import extend_schema_field


class CompanySerializer(serializers.ModelSerializer):
    """
    Primary serializer for the Company model.
    """
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'created_at', 'updated_at', 'user_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count']
    
    @extend_schema_field(serializers.IntegerField())
    def get_user_count(self, obj):
        """
        Returns the number of users associated with this company.
        """
        return obj.users.count() 