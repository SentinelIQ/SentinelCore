"""
Core audit logging functionality using django-auditlog.

This module provides mixins and decorators for integrating
audit logging into ViewSets, API views, and Celery tasks.
"""

import logging
from functools import wraps
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.contrib.contenttypes.models import ContentType
from rest_framework.serializers import ValidationError
from rest_framework import status

logger = logging.getLogger('audit')


def log_api_access(user, method, path, status_code, additional_data=None):
    """
    Log API access (typically GET requests) to the audit log.
    
    Args:
        user: The authenticated user (or None)
        method: HTTP method
        path: Request path
        status_code: Response status code
        additional_data: Additional data to include in the log entry
    """
    try:
        if additional_data is None:
            additional_data = {}
            
        # Ensure basic data is included
        additional_data.update({
            'request_method': method,
            'request_path': path,
            'response_status': status_code,
            'entity_type': 'api_access'
        })
        
        # Create log entry
        LogEntry.objects.create(
            # Content type is None for API access logs
            content_type=None,
            object_pk=None,
            object_repr=f"API Access: {method} {path}",
            action=LogEntry.Action.ACCESS,
            actor=user,
            additional_data=additional_data
        )
        
    except Exception as e:
        logger.error(f"Error logging API access: {str(e)}")


def log_api_view(user, method, path, status_code, additional_data=None):
    """
    Log API view calls (typically non-GET requests) to the audit log.
    
    Args:
        user: The authenticated user (or None)
        method: HTTP method
        path: Request path
        status_code: Response status code
        additional_data: Additional data to include in the log entry
    """
    try:
        if additional_data is None:
            additional_data = {}
            
        # Ensure basic data is included
        additional_data.update({
            'request_method': method,
            'request_path': path,
            'response_status': status_code,
            'entity_type': 'api_view'
        })
        
        # Map HTTP methods to LogEntry actions
        action_map = {
            'POST': LogEntry.Action.CREATE,
            'PUT': LogEntry.Action.UPDATE,
            'PATCH': LogEntry.Action.UPDATE,
            'DELETE': LogEntry.Action.DELETE,
            'GET': LogEntry.Action.ACCESS,
            'HEAD': LogEntry.Action.ACCESS,
            'OPTIONS': LogEntry.Action.ACCESS,
        }
        
        action = action_map.get(method, LogEntry.Action.CREATE)
        
        # Create log entry
        LogEntry.objects.create(
            # Content type is None for API view logs without specific model
            content_type=None,
            object_pk=None,
            object_repr=f"API View: {method} {path}",
            action=action,
            actor=user,
            additional_data=additional_data
        )
        
    except Exception as e:
        logger.error(f"Error logging API view: {str(e)}")


class AuditLogMixin:
    """
    Mixin to automatically log audit events for ViewSet actions.
    
    This mixin adds audit logging to the standard CRUD operations
    of a ViewSet: create, update, partial_update, and destroy.
    
    To use this mixin, add it to your ViewSet and define:
    - entity_type (str): The type of entity (e.g., 'alert', 'incident')
    
    Example:
    ```python
    class AlertViewSet(AuditLogMixin, viewsets.ModelViewSet):
        entity_type = 'alert'
        # ...
    ```
    """
    entity_type = None  # Must be set by the inheriting ViewSet
    
    def get_additional_log_data(self, request, obj=None, action=None):
        """
        Get additional data to include in the audit log.
        
        Override this method to add custom data to your audit logs.
        
        Args:
            request: The request object
            obj: The object being acted upon (optional)
            action: The action being performed (optional)
            
        Returns:
            dict: Additional data to include in the audit log
        """
        # Default implementation extracts entity type and company info
        data = {
            'client_ip': self._get_client_ip(request),
            'request_method': request.method,
            'request_path': request.path,
        }
        
        # Add entity type if available
        if hasattr(self, 'entity_type'):
            data['entity_type'] = self.entity_type
            
        # Add company info from the user if available
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                data['company_id'] = str(request.user.company.id)
                data['company_name'] = request.user.company.name
                
        return data
    
    def _get_client_ip(self, request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
        
    def create(self, request, *args, **kwargs):
        """Override create to add audit logging."""
        response = super().create(request, *args, **kwargs)
        
        # Log the creation action
        if response.status_code == status.HTTP_201_CREATED:
            obj = response.data
            self.log_create(request, obj)
            
        return response
    
    def update(self, request, *args, **kwargs):
        """Override update to add audit logging."""
        response = super().update(request, *args, **kwargs)
        
        # Log the update action
        if response.status_code == status.HTTP_200_OK:
            obj = self.get_object()
            self.log_update(request, obj)
            
        return response
    
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to add audit logging."""
        response = super().partial_update(request, *args, **kwargs)
        
        # Log the update action
        if response.status_code == status.HTTP_200_OK:
            obj = self.get_object()
            self.log_update(request, obj)
            
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to add audit logging."""
        obj = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        
        # Log the delete action
        if response.status_code == status.HTTP_204_NO_CONTENT:
            self.log_delete(request, obj)
            
        return response
    
    def log_create(self, request, obj):
        """
        Log a create action.
        
        Args:
            request: The request object
            obj: The object that was created
        """
        try:
            # Get additional data to include in the log
            additional_data = self.get_additional_log_data(request, obj, 'create')
            
            # Add response status
            additional_data['response_status'] = 'success'
            
            # Log the action using django-auditlog directly
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_pk=getattr(obj, 'id', str(obj)),
                object_repr=str(obj),
                action=LogEntry.Action.CREATE,
                actor=request.user,
                additional_data=additional_data
            )
        except Exception as e:
            logger.error(f"Error logging create action: {str(e)}")
    
    def log_update(self, request, obj):
        """
        Log an update action.
        
        Args:
            request: The request object
            obj: The object that was updated
        """
        try:
            # Get additional data to include in the log
            additional_data = self.get_additional_log_data(request, obj, 'update')
            
            # Add response status
            additional_data['response_status'] = 'success'
            
            # Log the action using django-auditlog
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_pk=getattr(obj, 'pk', str(obj)),
                object_repr=str(obj),
                action=LogEntry.Action.UPDATE,
                actor=request.user,
                additional_data=additional_data
            )
        except Exception as e:
            logger.error(f"Error logging update action: {str(e)}")
    
    def log_delete(self, request, obj):
        """
        Log a delete action.
        
        Args:
            request: The request object
            obj: The object that was deleted
        """
        try:
            # Get additional data to include in the log
            additional_data = self.get_additional_log_data(request, obj, 'delete')
            
            # Add response status
            additional_data['response_status'] = 'success'
            
            # Log the action using django-auditlog
            LogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(obj.__class__),
                object_pk=getattr(obj, 'pk', str(obj)),
                object_repr=str(obj),
                action=LogEntry.Action.DELETE,
                actor=request.user,
                additional_data=additional_data
            )
        except Exception as e:
            logger.error(f"Error logging delete action: {str(e)}")


def audit_action(action_type=None, entity_type=None):
    """
    Decorator to add audit logging to any function.
    
    This is useful for custom API actions that are not covered by the AuditLogMixin.
    
    Args:
        action_type (str): The type of action ('create', 'update', 'delete', 'custom')
        entity_type (str, optional): The type of entity. If None, tries to get from the view.
    
    Example:
    ```python
    @action(detail=True, methods=['post'])
    @audit_action(action_type='custom', entity_type='alert')
    def escalate(self, request, pk=None):
        # Custom action implementation
        pass
    ```
    """
    def decorator(func):
        @wraps(func)
        def wrapped(self, request, *args, **kwargs):
            # Map action type to LogEntry action constants
            action_map = {
                'create': LogEntry.Action.CREATE,
                'update': LogEntry.Action.UPDATE,
                'delete': LogEntry.Action.DELETE,
                'view': LogEntry.Action.ACCESS,
                'custom': LogEntry.Action.CREATE,  # Default for custom actions
            }
            audit_action_value = action_map.get(action_type, LogEntry.Action.CREATE)
            
            # Get entity type
            actual_entity_type = entity_type or getattr(self, 'entity_type', None)
            
            # Get instance if available
            instance = None
            if 'pk' in kwargs:
                # Try to get instance from the ViewSet's queryset
                if hasattr(self, 'get_object'):
                    try:
                        instance = self.get_object()
                    except Exception:
                        pass
            
            # Execute the original function
            try:
                response = func(self, request, *args, **kwargs)
                
                # Prepare additional data
                extra_data = {
                    'request_method': request.method,
                    'request_path': request.path,
                    'response_status': getattr(response, 'status_code', None),
                    'function_name': func.__name__,
                }
                
                # Add entity info
                if actual_entity_type:
                    extra_data['entity_type'] = actual_entity_type
                
                # Add custom action name
                if action_type == 'custom':
                    extra_data['custom_action'] = func.__name__
                
                # Log the action
                if instance:
                    # Log with instance
                    LogEntry.objects.log_create(
                        instance,
                        action=audit_action_value,
                        changes={},
                        actor=request.user if hasattr(request, 'user') else None,
                        additional_data=extra_data
                    )
                else:
                    # Log without specific instance
                    content_type = None
                    if hasattr(self, 'get_queryset') and self.get_queryset().exists():
                        model = self.get_queryset().model
                        content_type = ContentType.objects.get_for_model(model)
                    
                    LogEntry.objects.create(
                        content_type=content_type,
                        object_pk=str(kwargs.get('pk', '')),
                        object_repr=str(kwargs.get('pk', '')),
                        action=audit_action_value,
                        changes='{}',
                        actor=request.user if hasattr(request, 'user') else None,
                        additional_data=extra_data
                    )
                
                return response
                
            except Exception as e:
                # Log exception
                logger.error(f"Error in audited function {func.__name__}: {str(e)}")
                raise
                
        return wrapped
    return decorator


class AuditLogTaskMixin:
    """
    Mixin for Celery tasks to add audit logging capabilities.
    
    To use, add this mixin to your Task class and set entity_type:
    
    ```python
    class MyAuditedTask(AuditLogTaskMixin, celery.Task):
        entity_type = 'alert'
    ```
    """
    entity_type = 'task'  # Default entity type, should be overridden
    
    def on_success(self, retval, task_id, args, kwargs):
        """Log task success"""
        try:
            # Prepare log data
            extra_data = {
                'status': 'success',
                'task_id': task_id,
                'task_name': self.name,
                'args': str(args)[:250],  # Limit argument length
                'result': str(retval)[:250],  # Limit result length
                'entity_type': self.entity_type,
            }
            
            # Add company ID if available
            if 'company_id' in kwargs:
                extra_data['company_id'] = kwargs['company_id']
            
            # Log to django-auditlog
            LogEntry.objects.create(
                content_type=None,
                object_pk=task_id,
                object_repr=self.name,
                action=LogEntry.Action.UPDATE,
                changes='{}',
                actor=None,
                additional_data=extra_data
            )
            
        except Exception as e:
            logger.error(f"Error logging task success: {str(e)}")
            
            # Call parent method if exists
            super_on_success = getattr(super(), 'on_success', None)
            if super_on_success:
                super_on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure"""
        try:
            # Prepare log data
            extra_data = {
                'status': 'failure',
                'task_id': task_id,
                'task_name': self.name,
                'args': str(args)[:250],  # Limit argument length
                'error_type': type(exc).__name__,
                'error': str(exc)[:500],  # Limit error length
                'traceback': str(einfo)[:1000] if einfo else None,  # Limit traceback length
                'entity_type': self.entity_type,
            }
            
            # Add company ID if available
            if 'company_id' in kwargs:
                extra_data['company_id'] = kwargs['company_id']
            
            # Log to django-auditlog
            LogEntry.objects.create(
                content_type=None,
                object_pk=task_id,
                object_repr=self.name,
                action=LogEntry.Action.UPDATE,
                changes='{}',
                actor=None,
                additional_data=extra_data
            )
            
        except Exception as e:
            logger.error(f"Error logging task failure: {str(e)}")
            
            # Call parent method if exists
            super_on_failure = getattr(super(), 'on_failure', None)
            if super_on_failure:
                super_on_failure(exc, task_id, args, kwargs, einfo)
    
    def apply_async(self, args=None, kwargs=None, **options):
        """Log task start before dispatching"""
        try:
            args = args or ()
            kwargs = kwargs or {}
            
            # Get task ID if available or generate one
            task_id = options.get('task_id', f"task-{self.name}")
            
            # Prepare log data
            extra_data = {
                'status': 'started',
                'task_id': task_id,
                'task_name': self.name,
                'args': str(args)[:250],  # Limit argument length
                'entity_type': self.entity_type,
            }
            
            # Add company ID if available
            if 'company_id' in kwargs:
                extra_data['company_id'] = kwargs['company_id']
            
            # Log to django-auditlog
            LogEntry.objects.create(
                content_type=None,
                object_pk=task_id,
                object_repr=self.name,
                action=LogEntry.Action.CREATE,
                changes='{}',
                actor=None,
                additional_data=extra_data
            )
            
        except Exception as e:
            logger.error(f"Error logging task start: {str(e)}")
            
        # Continue with task dispatch
        return super().apply_async(args=args, kwargs=kwargs, **options)


def audit_task(entity_type=None):
    """
    Decorator to add audit logging to Celery tasks.
    
    This decorator adds audit logging to Celery tasks. It logs when 
    the task starts and finishes, including any errors.
    
    Args:
        entity_type: The type of entity being acted upon (optional)
        
    Returns:
        function: The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            task_name = func.__name__
            task_id = kwargs.get('task_id', 'unknown')
            
            # Prepare additional data
            additional_data = {
                'task_name': task_name,
                'task_id': task_id,
                'args': str(args),
                'kwargs': str(kwargs),
            }
            
            if entity_type:
                additional_data['entity_type'] = entity_type
            
            # Log task start
            try:
                logger.info(f"Starting task {task_name} with ID {task_id}")
                
                # Execute the task
                result = func(*args, **kwargs)
                
                # Log task completion
                logger.info(f"Completed task {task_name} with ID {task_id}")
                
                return result
                
            except Exception as e:
                # Log task error
                logger.error(f"Error in task {task_name} with ID {task_id}: {str(e)}")
                additional_data['error'] = str(e)
                additional_data['status'] = 'error'
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator


def get_entity_type_from_view(view_class):
    """
    Extracts entity_type from a view class.
    
    This function tries various ways to determine the entity type
    from a view class, useful for automatic audit logging.
    
    Args:
        view_class: The class of the view
        
    Returns:
        str: The entity type, or None if it can't be determined
    """
    # First check for explicit entity_type attribute
    if hasattr(view_class, 'entity_type') and view_class.entity_type:
        return view_class.entity_type
        
    # Check if it's a ViewSet with a queryset
    if hasattr(view_class, 'queryset') and view_class.queryset is not None:
        model = view_class.queryset.model
        if model:
            # Use model name as entity type
            return model.__name__.lower()
            
    # Try to get it from basename (for DefaultRouter)
    if hasattr(view_class, 'basename') and view_class.basename:
        return view_class.basename.replace('-', '_')
    
    # Fallback: try to extract from class name
    name = view_class.__name__
    if 'ViewSet' in name:
        name = name.replace('ViewSet', '')
    elif 'View' in name:
        name = name.replace('View', '')
        
    return name.lower() if name else None


def register_models_for_audit(app_list=None, exclude_models=None):
    """
    Register models from specified apps for audit logging.
    
    Args:
        app_list (list): List of Django app names to register for auditing
        exclude_models (list): List of specific models to exclude from auditing
            in format 'app_label.model_name'
    """
    if app_list is None:
        app_list = []
    
    if exclude_models is None:
        exclude_models = []
    
    # Default exclusions - models that shouldn't be audited
    default_exclusions = [
        'django.contrib.sessions.session',
        'django.contrib.admin.logentry',
        'django_celery_beat',
        'auditlog.logentry',
    ]
    
    exclude_models = exclude_models + default_exclusions
    
    # Get all installed models
    from django.apps import apps as django_apps
    all_models = django_apps.get_models()
    
    for model in all_models:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        model_path = f"{app_label}.{model_name}"
        
        # Skip excluded models
        if any(model_path.startswith(excluded) for excluded in exclude_models):
            continue
        
        # Register model if it belongs to specified apps or app_list is empty
        if not app_list or app_label in app_list:
            auditlog.register(model) 