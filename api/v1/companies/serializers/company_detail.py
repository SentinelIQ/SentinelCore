from .company_base import CompanySerializer
from .user_nested import UserNestedSerializer
from rest_framework import serializers
from companies.models import Company
from drf_spectacular.utils import extend_schema_field


class CompanyDetailSerializer(CompanySerializer):
    """
    Detailed serializer for Company, including associated users.
    """
    users = UserNestedSerializer(many=True, read_only=True)
    
    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + ['users']
        read_only_fields = CompanySerializer.Meta.read_only_fields + ['users']
    
    # Override with same type hint to satisfy drf-spectacular
    @extend_schema_field(serializers.IntegerField())
    def get_user_count(self, obj):
        """
        Returns the number of users associated with this company.
        """
        return obj.users.count() 