from rest_framework import serializers
from companies.models import Company


class CompanySerializer(serializers.ModelSerializer):
    """
    Primary serializer for the Company model.
    """
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'created_at', 'updated_at', 'user_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count']
    
    def get_user_count(self, obj):
        """
        Returns the number of users associated with this company.
        """
        return obj.users.count() 