from rest_framework import serializers
from wiki.models import KnowledgeArticle
import markdown2
from drf_spectacular.utils import extend_schema_field


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for KnowledgeArticle model.
    """
    html_content = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeArticle
        fields = [
            'id', 'title', 'slug', 'content', 'html_content',
            'visibility', 'category', 'category_name', 'tags',
            'company', 'author', 'author_name',
            'created_at', 'updated_at', 'published_at', 'expires_at',
            'is_reviewed', 'version'
        ]
        read_only_fields = ['id', 'html_content', 'author_name', 'category_name',
                          'created_at', 'updated_at', 'version', 'author']
    
    @extend_schema_field(serializers.CharField())
    def get_html_content(self, obj):
        """
        Convert Markdown content to HTML.
        """
        if obj.content:
            return markdown2.markdown(
                obj.content,
                extras=["tables", "code-friendly", "fenced-code-blocks"]
            )
        return ""
    
    @extend_schema_field(serializers.CharField())
    def get_author_name(self, obj):
        """
        Get the author's display name.
        """
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}" if obj.author.first_name else obj.author.username
        return "Unknown"
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_category_name(self, obj):
        """
        Get the category name.
        """
        if obj.category:
            return obj.category.name
        return None
    
    def validate(self, attrs):
        """
        Validate that the article meets the required constraints.
        """
        request = self.context.get('request')
        company = attrs.get('company')
        visibility = attrs.get('visibility')
        
        # Public articles should not have a company
        if visibility == KnowledgeArticle.Visibility.PUBLIC:
            attrs['company'] = None
        
        # Private articles must have a company
        elif visibility == KnowledgeArticle.Visibility.PRIVATE and not company:
            # If user has a company, use it
            if request and request.user and hasattr(request.user, 'company') and request.user.company:
                attrs['company'] = request.user.company
            else:
                raise serializers.ValidationError({
                    'company': 'Private articles must be associated with a company.'
                })
        
        # Company users can only create articles for their company
        if not request.user.is_superuser and hasattr(request.user, 'company') and company:
            if request.user.company != company:
                raise serializers.ValidationError({
                    'company': 'You can only create articles for your own company.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a new article and set the author.
        """
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
        
        return super().create(validated_data) 