from .company_base import CompanySerializer
from .user_nested import UserNestedSerializer


class CompanyDetailSerializer(CompanySerializer):
    """
    Detailed serializer for Company, including associated users.
    """
    users = UserNestedSerializer(many=True, read_only=True)
    
    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + ['users'] 