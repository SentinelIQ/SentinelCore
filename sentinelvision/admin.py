from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils.text import capfirst
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.http import HttpResponseRedirect

from sentinelvision.feeds import get_all_feeds, get_all_feed_tasks, get_feed_class
from sentinelvision.models import (
    FeedModule, AnalyzerModule, ResponderModule,
    FeedRegistry, ExecutionRecord, FeedExecutionRecord, ExecutionStatusEnum, ExecutionSourceEnum,
    EnrichedIOC, IOCFeedMatch
)

# Registry for feed module admin classes
class FeedModuleAdminRegistry:
    """
    Registry for feed module admin classes.
    This ensures a single admin interface for all feed types.
    """
    @classmethod
    def register(cls):
        """Register FeedModule and all its subclasses with a single admin."""
        class FeedModuleAdmin(admin.ModelAdmin):
            """
            Admin for feed modules with dynamic feed type discovery.
            This admin provides a unified interface for all feed types.
            """
            list_display = ('name', 'module_type_display', 'company', 'is_active', 'last_run_display', 'total_iocs_display', 'feed_actions')
            list_filter = ('is_active', 'company')
            search_fields = ('name', 'description')
            readonly_fields = ('name', 'module_type', 'last_run', 'last_error', 'error_count', 'total_processed', 'success_rate', 'total_iocs_imported')
            fieldsets = (
                (None, {
                    'fields': ('name', 'description', 'is_active', 'company')
                }),
                ('Feed Configuration', {
                    'fields': ('feed_url', 'interval_hours', 'auto_mark_as_ioc', 'cron_schedule')
                }),
                ('Status & Metrics', {
                    'fields': ('last_run', 'last_error', 'error_count', 'total_processed', 'success_rate', 'total_iocs_imported')
                }),
            )
            
            def has_add_permission(self, request):
                """
                Disable the ability to manually add feed modules.
                Feed modules are automatically created based on the feeds directory.
                """
                return False
                
            def has_delete_permission(self, request, obj=None):
                """
                Disable the ability to delete feed modules.
                Feed modules should only be managed programmatically.
                """
                return False
                
            def get_readonly_fields(self, request, obj=None):
                """
                Make the name and module_type fields read-only.
                """
                readonly = list(self.readonly_fields)
                if obj:  # Editing an existing object
                    readonly.extend(['name', 'module_type'])
                return readonly
                
            def changelist_view(self, request, extra_context=None):
                """
                Add a message to the changelist view explaining how feeds work.
                """
                extra_context = extra_context or {}
                extra_context['feeds_help_text'] = (
                    "Feed modules are defined in the code and cannot be created through this interface. "
                    "Available feeds are automatically discovered from the feeds directory. "
                    "You can only modify the configuration of existing feeds."
                )
                return super().changelist_view(request, extra_context=extra_context)
            
            def module_type_display(self, obj):
                """Get module type for display."""
                # Try to get more specific type
                module_type = getattr(obj, 'feed_type', obj.module_type)
                return module_type.replace('_', ' ').title()
            
            module_type_display.short_description = 'Type'
            
            def total_iocs_display(self, obj):
                """Get total IOCs imported for display."""
                if hasattr(obj, 'total_iocs_imported'):
                    return obj.total_iocs_imported
                return 0
                
            total_iocs_display.short_description = 'IOCs Imported'
            
            def last_run_display(self, obj):
                """Format last run time for display."""
                if obj.last_run:
                    return obj.last_run.strftime('%Y-%m-%d %H:%M')
                return '-'
                
            last_run_display.short_description = 'Last Run'
            
            def feed_actions(self, obj):
                """Render action buttons for feed."""
                run_url = reverse('admin:run_feed', args=[obj.pk])
                history_url = reverse('admin:feed_history', args=[obj.pk])
                
                buttons = f"""
                <a href="{run_url}" class="button" title="Run Feed Now">
                    <i class="fa fa-play"></i> Run
                </a>
                <a href="{history_url}" class="button" title="View Execution History">
                    <i class="fa fa-history"></i> History
                </a>
                """
                
                # Show a label if the feed is global
                if obj.company is None:
                    buttons += '<span class="label label-info" style="margin-left: 5px; background-color: #5bc0de; color: white; padding: 2px 5px; border-radius: 3px;">Global</span>'
                    
                return mark_safe(buttons)
                
            feed_actions.short_description = 'Actions'
            
            def get_urls(self):
                """Add custom URLs for feed actions."""
                urls = super().get_urls()
                custom_urls = [
                    path(
                        '<uuid:feed_id>/run/',
                        self.admin_site.admin_view(self.run_feed_view),
                        name='run_feed'
                    ),
                    path(
                        '<uuid:feed_id>/history/',
                        self.admin_site.admin_view(self.feed_history_view),
                        name='feed_history'
                    ),
                ]
                return custom_urls + urls
                
            def run_feed_view(self, request, feed_id):
                """
                View for running a feed manually.
                
                Args:
                    request: The HTTP request
                    feed_id: UUID of feed to run
                
                Returns:
                    HttpResponse
                """
                from sentinelvision.tasks import run_feed_task
                
                feed = self.get_object(request, feed_id)
                if feed is None:
                    return self._get_obj_does_not_exist_redirect(
                        request, self.model._meta, feed_id
                    )
                
                # Check permissions
                if not self._can_run_feed(request, feed):
                    messages.error(
                        request,
                        "You don't have permission to run this feed. Global feeds can only be run by superadmins."
                    )
                    return HttpResponseRedirect(
                        reverse('admin:sentinelvision_feedmodule_change', args=[feed_id])
                    )
                
                if request.method != 'POST':
                    # Confirmation page
                    context = {
                        'title': f'Run Feed: {feed.name}',
                        'feed': feed,
                        'is_global': feed.company is None,
                        'opts': self.model._meta,
                        'app_label': self.model._meta.app_label,
                    }
                    return render(
                        request,
                        'admin/sentinelvision/feedmodule/run_confirmation.html',
                        context
                    )
                
                # Handle POST (confirmed run)
                
                # Create execution record
                execution_record = FeedExecutionRecord.objects.create(
                    feed=feed,
                    executed_by=request.user,
                    source=ExecutionSourceEnum.MANUAL,
                    status=ExecutionStatusEnum.PENDING,
                    started_at=timezone.now()
                )
                
                # Run feed task asynchronously
                company_id = str(feed.company.id) if feed.company else None
                task = run_feed_task.delay(
                    feed_id=str(feed.id),
                    execution_record_id=str(execution_record.id),
                    company_id=company_id
                )
                
                messages.success(
                    request,
                    f"Feed '{feed.name}' execution started. Refresh the page to see updated status."
                )
                
                return HttpResponseRedirect(
                    reverse('admin:feed_history', args=[feed_id])
                )
                
            def feed_history_view(self, request, feed_id):
                """
                View for feed execution history.
                
                Args:
                    request: The HTTP request
                    feed_id: UUID of feed
                
                Returns:
                    HttpResponse
                """
                feed = self.get_object(request, feed_id)
                if feed is None:
                    return self._get_obj_does_not_exist_redirect(
                        request, self.model._meta, feed_id
                    )
                
                # Get all execution records for this feed
                execution_records = FeedExecutionRecord.objects.filter(
                    feed=feed
                ).select_related('executed_by').order_by('-started_at')
                
                context = {
                    'title': f'Execution History: {feed.name}',
                    'feed': feed,
                    'execution_records': execution_records,
                    'opts': self.model._meta,
                    'app_label': self.model._meta.app_label,
                }
                
                return render(
                    request,
                    'admin/sentinelvision/feedmodule/execution_history.html',
                    context
                )
                
            def _can_run_feed(self, request, feed):
                """
                Check if user can run a feed.
                
                Args:
                    request: The HTTP request
                    feed: The feed module
                
                Returns:
                    bool: True if user can run feed
                """
                user = request.user
                
                # Superusers can run any feed
                if user.is_superuser:
                    return True
                    
                # For company-specific feeds, check if user belongs to that company
                if feed.company:
                    return getattr(user, 'company', None) == feed.company
                    
                # For global feeds, only superusers can run
                return False
                
        # Register the admin class for FeedModule
        admin.site.register(FeedModule, FeedModuleAdmin)

# Register the feed modules with admin
FeedModuleAdminRegistry.register()


@admin.register(AnalyzerModule)
class AnalyzerModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'analysis_type', 'company', 'is_active', 'last_run', 'total_analyses')
    list_filter = ('is_active', 'analysis_type', 'company')
    search_fields = ('name', 'description')
    readonly_fields = ('last_run', 'last_error', 'error_count', 'total_analyses', 'total_findings', 'average_confidence')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active', 'company')
        }),
        ('Analyzer Configuration', {
            'fields': ('analysis_type', 'confidence_threshold', 'max_analysis_time')
        }),
        ('Status', {
            'fields': ('last_run', 'last_error', 'error_count', 'total_analyses', 'total_findings', 'average_confidence')
        }),
    )


@admin.register(ResponderModule)
class ResponderModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'response_type', 'company', 'is_active', 'last_run', 'total_responses')
    list_filter = ('is_active', 'response_type', 'severity_threshold', 'company')
    search_fields = ('name', 'description')
    readonly_fields = ('last_run', 'last_error', 'error_count', 'total_responses', 'total_successful', 'total_failed')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active', 'company')
        }),
        ('Responder Configuration', {
            'fields': ('response_type', 'severity_threshold', 'api_key', 'api_url', 'configuration')
        }),
        ('Status', {
            'fields': ('last_run', 'last_error', 'error_count', 'total_responses', 'total_successful', 'total_failed')
        }),
    )


@admin.register(FeedRegistry)
class FeedRegistryAdmin(admin.ModelAdmin):
    list_display = ('name', 'feed_type', 'company', 'enabled', 'sync_status', 'last_sync', 'total_iocs')
    list_filter = ('feed_type', 'company', 'enabled', 'sync_status')
    search_fields = ('name', 'description', 'source_url')
    readonly_fields = ('last_sync', 'next_sync', 'sync_status', 'total_iocs', 'last_import_count', 
                      'total_imports', 'error_count', 'last_error', 'last_log', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'feed_type', 'source_url', 'enabled', 'company')
        }),
        ('Sync Configuration', {
            'fields': ('sync_interval_hours', 'headers', 'parser_options', 'config')
        }),
        ('Sync Status', {
            'fields': ('sync_status', 'last_sync', 'next_sync', 'last_error', 'last_log')
        }),
        ('Statistics', {
            'fields': ('total_iocs', 'last_import_count', 'total_imports', 'error_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['enable_feeds', 'disable_feeds', 'trigger_feed_sync', 'update_all_feeds', 'update_with_dispatcher', 'update_specific_feed_type']
    
    def enable_feeds(self, request, queryset):
        """Admin action to enable selected feeds"""
        updated = queryset.update(enabled=True)
        self.message_user(request, f"{updated} feeds were enabled.")
    enable_feeds.short_description = "Enable selected feeds"
    
    def disable_feeds(self, request, queryset):
        """Admin action to disable selected feeds"""
        updated = queryset.update(
            enabled=False,
            sync_status=FeedRegistry.SyncStatus.DISABLED
        )
        self.message_user(request, f"{updated} feeds were disabled.")
    disable_feeds.short_description = "Disable selected feeds"
    
    def trigger_feed_sync(self, request, queryset):
        """Admin action to trigger immediate synchronization"""
        from sentinelvision.tasks.feed_tasks import update_feed
        
        count = 0
        for feed in queryset:
            update_feed.apply_async(args=[str(feed.id)])
            count += 1
        
        self.message_user(request, f"Triggered sync for {count} feeds.")
    trigger_feed_sync.short_description = "Trigger sync for selected feeds"
    
    def update_all_feeds(self, request, queryset):
        """Admin action to update all feed types for selected companies"""
        from sentinelvision.feeds import get_all_feed_tasks
        
        # Get unique companies from selected feed registries
        company_ids = queryset.values_list('company_id', flat=True).distinct()
        feed_tasks = get_all_feed_tasks()
        
        total_tasks = 0
        
        for company_id in company_ids:
            for feed_id, feed_task in feed_tasks.items():
                feed_task.delay(company_id)
                total_tasks += 1
        
        self.message_user(request, f"Triggered {len(feed_tasks)} feed types update for {len(company_ids)} companies. Total tasks: {total_tasks}")
    update_all_feeds.short_description = "Update ALL feed types for selected companies"
    
    def update_with_dispatcher(self, request, queryset):
        """Admin action to update all feed types using the centralized dispatcher"""
        from sentinelvision.tasks.feed_dispatcher import update_all_feeds
        
        # Get unique companies from selected feed registries
        company_ids = queryset.values_list('company_id', flat=True).distinct()
        count = len(company_ids)
        
        if count > 0:
            for company_id in company_ids:
                update_all_feeds.delay(company_id=company_id, concurrent=True)
            
            self.message_user(request, f"Triggered centralized feed dispatcher for {count} companies.")
        else:
            self.message_user(request, "No companies selected for feed updates.")
    update_with_dispatcher.short_description = "Update using centralized dispatcher"
    
    def update_specific_feed_type(self, request, queryset):
        """Admin action to update a specific feed type for selected companies"""
        from sentinelvision.feeds import get_all_feeds, get_feed_task
        from django.contrib.admin.helpers import ActionForm
        from django import forms
        
        # Get available feed types for dropdown
        feeds = get_all_feeds()
        feed_choices = [(feed_id, f"{feed_class._meta.verbose_name} ({feed_id})") 
                        for feed_id, feed_class in feeds.items()]
        
        class FeedChoiceForm(ActionForm):
            feed_type = forms.ChoiceField(choices=feed_choices, label="Feed Type")
        
        self.action_form = FeedChoiceForm
        
        if 'feed_type' in request.POST:
            feed_type = request.POST.get('feed_type')
            feed_task = get_feed_task(feed_type)
            
            if not feed_task:
                self.message_user(request, f"Feed type '{feed_type}' not found", level="ERROR")
                return
            
            # Get unique companies from selected feed registries
            company_ids = queryset.values_list('company_id', flat=True).distinct()
            count = 0
            
            for company_id in company_ids:
                feed_task.delay(company_id)
                count += 1
            
            self.message_user(request, f"Triggered {feed_type} feed update for {count} companies.")
    update_specific_feed_type.short_description = "Update specific feed type for selected companies"


@admin.register(ExecutionRecord)
class ExecutionRecordAdmin(admin.ModelAdmin):
    """Admin configuration for execution records"""
    list_display = ('module_name', 'module_type', 'started_at', 'completed_at', 'status', 'duration')
    list_filter = ('module_type', 'status', 'started_at')
    search_fields = ('module_name', 'execution_log')
    readonly_fields = ('module_name', 'module_type', 'started_at', 'completed_at', 'status', 'execution_log', 'error_message')
    fieldsets = (
        (None, {
            'fields': ('module_name', 'module_type', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Details', {
            'fields': ('execution_log', 'error_message')
        }),
    )
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            return obj.completed_at - obj.started_at
        return "N/A"
    duration.short_description = "Duration"
    
    def has_add_permission(self, request):
        return False


def list_feed_tasks_view(request):
    """Custom admin view to display available feed tasks."""
    tasks = get_all_feed_tasks()
    feed_data = [
        {
            'id': task_id,
            'name': task.__name__,
            'module': task.__module__,
            'docs': task.__doc__ or 'No documentation'
        } for task_id, task in tasks.items()
    ]
    
    return JsonResponse({'feed_tasks': feed_data})

# Use Django's built-in admin URL patterns
from django.urls import path

# Add custom admin view via get_urls()
admin_urls = admin.site.get_urls
def get_custom_urls():
    urls = admin_urls()
    custom_urls = [
        path('feed-tasks/', admin.site.admin_view(list_feed_tasks_view), name='list_feed_tasks'),
    ]
    return custom_urls + urls

admin.site.get_urls = get_custom_urls

@admin.register(FeedExecutionRecord)
class FeedExecutionRecordAdmin(admin.ModelAdmin):
    """Admin interface for feed execution records."""
    list_display = (
        'feed_name', 'source', 'status', 'started_at', 
        'ended_at', 'duration_display', 'iocs_processed'
    )
    list_filter = ('status', 'source', 'feed', 'executed_by')
    search_fields = ('feed__name', 'error_message', 'log')
    readonly_fields = (
        'feed', 'executed_by', 'source', 'status', 'started_at',
        'ended_at', 'duration_display', 'iocs_processed', 
        'error_message', 'log'
    )
    date_hierarchy = 'started_at'
    ordering = ('-started_at',)
    
    def feed_name(self, obj):
        """Get the name of the feed."""
        return obj.feed.name
    feed_name.short_description = 'Feed'
    feed_name.admin_order_field = 'feed__name'
    
    def duration_display(self, obj):
        """Format duration for display."""
        if obj.duration_seconds is not None:
            # Format as minutes:seconds if over 60 seconds
            if obj.duration_seconds >= 60:
                minutes = int(obj.duration_seconds // 60)
                seconds = int(obj.duration_seconds % 60)
                return f"{minutes}m {seconds}s"
            # Format as seconds with 2 decimal places
            return f"{obj.duration_seconds:.2f}s"
        return '-'
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        """Disable manual creation of execution records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of execution records."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of execution records."""
        return True

@admin.register(EnrichedIOC)
class EnrichedIOCAdmin(admin.ModelAdmin):
    """Admin interface for enriched IOCs."""
    list_display = (
        'ioc_value_display', 'ioc_type', 'company', 'status', 
        'confidence_display', 'match_count', 'first_seen', 'last_checked'
    )
    list_filter = ('status', 'ioc_type', 'company', 'tlp', 'source')
    search_fields = ('value', 'description', 'tags')
    readonly_fields = (
        'first_seen', 'last_checked', 'last_matched', 'confidence',
        'tags', 'matched_feeds', 'es_index', 'es_doc_id', 'match_count'
    )
    fieldsets = (
        (None, {
            'fields': ('company', 'ioc_type', 'value', 'status', 'source')
        }),
        ('Enrichment', {
            'fields': ('first_seen', 'last_checked', 'last_matched', 
                      'confidence', 'tlp', 'tags', 'match_count')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Elasticsearch', {
            'fields': ('es_index', 'es_doc_id'),
            'classes': ('collapse',)
        })
    )
    
    def ioc_value_display(self, obj):
        """Format IOC value for display."""
        max_length = 50
        if len(obj.value) > max_length:
            return f"{obj.value[:max_length]}..."
        return obj.value
    ioc_value_display.short_description = 'IOC Value'
    ioc_value_display.admin_order_field = 'value'
    
    def confidence_display(self, obj):
        """Format confidence score for display."""
        if obj.confidence:
            return f"{obj.confidence:.2f}"
        return "-"
    confidence_display.short_description = 'Confidence'
    confidence_display.admin_order_field = 'confidence'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        return super().get_queryset(request).prefetch_related('matched_feeds')


@admin.register(IOCFeedMatch)
class IOCFeedMatchAdmin(admin.ModelAdmin):
    """Admin interface for IOC-Feed matches."""
    list_display = ('ioc_display', 'feed', 'match_time', 'feed_confidence')
    list_filter = ('feed', 'match_time')
    search_fields = ('ioc__value',)
    readonly_fields = ('match_time', 'feed_confidence', 'feed_tags', 'metadata')
    fieldsets = (
        (None, {
            'fields': ('ioc', 'feed')
        }),
        ('Match Details', {
            'fields': ('match_time', 'feed_confidence', 'feed_tags')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def ioc_display(self, obj):
        """Format IOC for display."""
        max_length = 40
        value = obj.ioc.value
        if len(value) > max_length:
            return f"{obj.ioc.get_ioc_type_display()}: {value[:max_length]}..."
        return f"{obj.ioc.get_ioc_type_display()}: {value}"
    ioc_display.short_description = 'IOC'
    
    def has_add_permission(self, request):
        """Disable manual creation of matches."""
        return False
