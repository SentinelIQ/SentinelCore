from django.contrib import admin
from .models import Observable, ObservableRelationship
from api.v1.observables.enums import ObservableTypeEnum, ObservableCategoryEnum
from api.core.utils.enum_utils import enum_to_choices


@admin.register(Observable)
class ObservableAdmin(admin.ModelAdmin):
    list_display = ('display_type', 'value', 'category', 'company', 'is_ioc', 'created_at')
    list_filter = ('type', 'category', 'is_ioc', 'is_false_positive', 'company', 'created_at')
    search_fields = ('value', 'description', 'source')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'type', 'value', 'description', 'category')
        }),
        ('Status', {
            'fields': ('is_ioc', 'is_false_positive', 'confidence')
        }),
        ('Temporal Information', {
            'fields': ('first_seen', 'last_seen')
        }),
        ('Relationships', {
            'fields': ('company', 'created_by', 'alert', 'incident')
        }),
        ('Classification', {
            'fields': ('tags', 'tlp', 'source')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Enrichment', {
            'fields': ('enrichment_data',),
            'classes': ('collapse',)
        }),
    )
    
    def display_type(self, obj):
        """Display the readable type of the observable."""
        return obj.get_type_display()
    display_type.short_description = 'Type'
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "type":
            # Customize the type dropdown to show both code and display name
            kwargs['choices'] = [(t[0], f"{t[1]} ({t[0]})") for t in enum_to_choices(ObservableTypeEnum)]
        elif db_field.name == "category":
            # Customize the category dropdown to show both code and display name
            kwargs['choices'] = [(c[0], f"{c[1]} ({c[0]})") for c in enum_to_choices(ObservableCategoryEnum)]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


@admin.register(ObservableRelationship)
class ObservableRelationshipAdmin(admin.ModelAdmin):
    list_display = ('source', 'relationship_type_display', 'target', 'company', 'created_at')
    list_filter = ('relationship_type', 'company', 'created_at')
    search_fields = ('source__value', 'target__value', 'description')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Relationship', {
            'fields': ('id', 'source', 'relationship_type', 'target', 'description')
        }),
        ('Organization', {
            'fields': ('company', 'created_by')
        }),
        ('Additional Data', {
            'fields': ('tags', 'metadata')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def relationship_type_display(self, obj):
        """Display the readable relationship type."""
        return obj.get_relationship_type_display()
    relationship_type_display.short_description = 'Relationship Type' 