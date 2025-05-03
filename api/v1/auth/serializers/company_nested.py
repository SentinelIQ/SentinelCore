from rest_framework import serializers
from companies.models import Company


class CompanyNestedSerializer(serializers.ModelSerializer):
    """
    Simplified Company serializer used in UserSerializer.
    """
    class Meta:
        model = Company
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = fields 