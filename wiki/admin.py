from django.contrib import admin
from .models import KnowledgeArticle, KnowledgeCategory


@admin.register(KnowledgeCategory)
class KnowledgeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'company', 'created_at')
    list_filter = ('company', 'parent')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    list_per_page = 20


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'visibility', 'company', 
                    'author', 'is_published', 'is_reviewed', 'created_at', 'updated_at')
    list_filter = ('visibility', 'company', 'category', 'is_reviewed', 'tags')
    search_fields = ('title', 'slug', 'content', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'version')
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'content')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Visibility', {
            'fields': ('visibility', 'company')
        }),
        ('Authorship', {
            'fields': ('author',)
        }),
        ('Publication', {
            'fields': ('published_at', 'expires_at')
        }),
        ('Quality Control', {
            'fields': ('is_reviewed', 'last_reviewed_by', 'version')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Auto-set author and increment version on change.
        """
        if not change:  # New object
            obj.author = request.user
        else:
            obj.version += 1
            
        super().save_model(request, obj, form, change)
