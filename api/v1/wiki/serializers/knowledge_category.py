from rest_framework import serializers
from wiki.models import KnowledgeCategory


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for KnowledgeCategory model.
    """
    class Meta:
        model = KnowledgeCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 
            'company', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate(self, attrs):
        """
        Validate that the category belongs to the user's company or is global.
        """
        request = self.context.get('request')
        company = attrs.get('company')
        
        # Allow superusers to create categories for any company
        if request and request.user and request.user.is_superuser:
            return attrs
            
        # For company users, ensure they can only create categories for their company
        if request and request.user and hasattr(request.user, 'company') and company:
            if request.user.company != company:
                raise serializers.ValidationError({
                    'company': 'You can only create categories for your own company.'
                })
        
        return attrs 