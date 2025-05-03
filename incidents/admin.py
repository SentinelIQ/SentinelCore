from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from .models import Incident, TimelineEvent, IncidentObservable, IncidentTask
from observables.models import Observable
from api.v1.observables.enums import ObservableTypeEnum
from api.core.utils.enum_utils import enum_to_choices


# Custom form for adding observables
class AddObservableForm(forms.Form):
    """Custom form for adding observables to an incident."""
    observable_type = forms.ChoiceField(
        choices=enum_to_choices(ObservableTypeEnum),
        label="Observable type",
        help_text="Select the observable type"
    )
    value = forms.CharField(
        max_length=500,
        label="Value",
        help_text="Enter the observable value (e.g. email address, domain, IP, etc.)",
        widget=forms.TextInput(attrs={'size': '60'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}), 
        label="Description",
        help_text="Optional description for this observable"
    )
    is_ioc = forms.BooleanField(
        required=False, 
        label="Is this an IOC (Indicator of Compromise)?",
        initial=True
    )


class IncidentObservableAdminForm(admin.ModelAdmin):
    """Custom form for IncidentObservable with better display of observable types and values."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This will be done when a form instance is created
        if 'observable' in self.fields:
            self.fields['observable'].queryset = Observable.objects.all().order_by('type', 'value')
            self.fields['observable'].label_from_instance = lambda obj: f"{obj.get_type_display()}: {obj.value}"


class IncidentObservableInline(admin.TabularInline):
    model = IncidentObservable
    extra = 1
    fields = ('observable', 'display_type', 'display_value', 'is_ioc', 'description')
    readonly_fields = ('display_type', 'display_value')
    verbose_name = "Observable"
    verbose_name_plural = "Observables"
    
    def display_type(self, obj):
        """Display the readable type of the observable."""
        if obj.observable:
            return format_html('<span style="font-weight: bold;">{}</span>', obj.observable.get_type_display())
        return ""
    display_type.short_description = 'Type'
    
    def display_value(self, obj):
        """Display the value of the observable."""
        if obj.observable:
            return obj.observable.value
        return ""
    display_value.short_description = 'Value'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "observable":
            # Customize observable display in dropdown
            from django.forms.models import ModelChoiceField
            
            # Customize the queryset
            queryset = db_field.related_model.objects.all().order_by('type', 'value')
            
            # Create a ModelChoiceField
            field = ModelChoiceField(queryset=queryset)
            
            # Set the label_from_instance method on the field
            field.label_from_instance = lambda obj: f"{obj.get_type_display()}: {obj.value}"
            
            # Return the customized field
            return field
            
        # For other foreign keys, use the default behavior
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class IncidentTaskInline(admin.TabularInline):
    model = IncidentTask
    extra = 1
    fields = ('title', 'description', 'status', 'priority', 'assignee', 'due_date')
    verbose_name = "Task"
    verbose_name_plural = "Tasks"


class TimelineEventInline(admin.TabularInline):
    model = TimelineEvent
    extra = 0
    fields = ('type', 'title', 'message', 'timestamp', 'user')
    readonly_fields = ('type', 'title', 'message', 'timestamp', 'user')
    can_delete = False
    max_num = 0  # Don't allow adding new events directly
    verbose_name = "Timeline Event"
    verbose_name_plural = "Timeline Events"
    ordering = ('-timestamp',)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'status', 'company', 'created_by', 'created_at')
    list_filter = ('severity', 'status', 'company', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [IncidentObservableInline, IncidentTaskInline, TimelineEventInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'summary', 'severity', 'status')
        }),
        ('Relationships', {
            'fields': ('company', 'created_by', 'assignee')
        }),
        ('MITRE ATT&CK', {
            'fields': ('primary_technique', 'sub_technique'),
            'description': 'MITRE ATT&CK techniques and sub-techniques associated with this incident'
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
        ('Classification', {
            'fields': ('tags', 'tlp', 'pap', 'impact_score')
        }),
        ('Advanced', {
            'fields': ('timeline', 'custom_fields', 'linked_entities', 'sentinelvision_responders'),
            'classes': ('collapse',)
        })
    )


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident', 'type', 'timestamp', 'user')
    list_filter = ('type', 'timestamp', 'incident__company')
    search_fields = ('title', 'message', 'incident__title')
    readonly_fields = ('id', 'created_at', 'formatted_metadata')
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'incident', 'type', 'title', 'message', 'timestamp')
        }),
        ('Relationships', {
            'fields': ('user', 'company')
        }),
        ('Metadata', {
            'fields': ('formatted_metadata',)
        }),
        ('System', {
            'fields': ('created_at',)
        }),
    )
    
    def formatted_metadata(self, obj):
        """Format the JSON metadata for better readability."""
        if not obj.metadata:
            return "No metadata"
        
        try:
            import json
            formatted = json.dumps(obj.metadata, indent=4)
            return mark_safe(f'<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{formatted}</pre>')
        except Exception as e:
            return f"Error formatting metadata: {str(e)}"
    
    formatted_metadata.short_description = "Metadata (Formatted)"


@admin.register(IncidentObservable)
class IncidentObservableAdmin(admin.ModelAdmin):
    list_display = ('incident', 'observable_type', 'observable_value', 'is_ioc', 'created_at')
    list_filter = ('is_ioc', 'observable__type', 'created_at', 'incident__company')
    search_fields = ('incident__title', 'observable__value')
    readonly_fields = ('id', 'created_at')
    
    def observable_type(self, obj):
        """Display the readable type of the observable."""
        return obj.observable.get_type_display()
    observable_type.short_description = 'Type'
    
    def observable_value(self, obj):
        """Display the value of the observable."""
        return obj.observable.value
    observable_value.short_description = 'Value'


@admin.register(IncidentTask)
class IncidentTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident', 'status', 'priority', 'assignee', 'due_date')
    list_filter = ('status', 'priority', 'due_date', 'incident__company')
    search_fields = ('title', 'description', 'incident__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at') 