import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.v1.audit_logs.enums import EntityTypeEnum, ActionTypeEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()


class AuditLog(CoreModel):
    """
    AuditLog model for tracking all critical actions in the system.
    Maintains a detailed audit trail for security and compliance purposes.
    """
    
    # Who performed the action
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs',
        verbose_name='User'
    )
    username = models.CharField(
        max_length=150, 
        blank=True, 
        null=True,
        help_text='Username at the time of the action (in case user is deleted)'
    )
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True,
        verbose_name='IP Address'
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        verbose_name='User Agent'
    )
    
    # What was done
    action = models.CharField(
        max_length=50, 
        choices=enum_to_choices(ActionTypeEnum),
        verbose_name='Action'
    )
    action_details = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Action Details'
    )
    
    # To what entity
    entity_type = models.CharField(
        max_length=50, 
        choices=enum_to_choices(EntityTypeEnum),
        verbose_name='Entity Type'
    )
    entity_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name='Entity ID'
    )
    entity_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Entity Name',
        help_text='Name or title of the entity at the time of the action'
    )
    
    # Associated company for tenant isolation
    company_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name='Company ID'
    )
    company_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Company Name'
    )
    
    # Request/response details
    request_method = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name='Request Method'
    )
    request_path = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name='Request Path'
    )
    request_data = models.JSONField(
        blank=True, 
        null=True,
        verbose_name='Request Data'
    )
    response_status = models.PositiveSmallIntegerField(
        blank=True, 
        null=True,
        verbose_name='Response Status'
    )
    
    # Additional data for specific actions
    additional_data = models.JSONField(
        blank=True, 
        null=True,
        verbose_name='Additional Data'
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        'Timestamp',
        default=timezone.now,
        help_text='When the action occurred'
    )
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['company_id']),
        ]
    
    def __str__(self):
        entity_info = f"{self.entity_name}" if self.entity_name else f"{self.entity_type}:{self.entity_id}"
        user_info = self.username or (self.user.username if self.user else "System")
        return f"{user_info} - {self.get_action_display()} - {entity_info}"
    
    @classmethod
    def log_action(cls, user, action, entity_type, entity_id=None, entity_name=None, 
                  request=None, response_status=None, additional_data=None, company=None):
        """
        Create an audit log entry.
        
        Args:
            user (User): The user who performed the action
            action (str): The action performed
            entity_type (str): The type of entity the action was performed on
            entity_id (str, optional): The ID of the entity
            entity_name (str, optional): The name of the entity
            request (HttpRequest, optional): The request object
            response_status (int, optional): The HTTP response status code
            additional_data (dict, optional): Additional data relevant to the action
            company (Company, optional): The company associated with the action
        
        Returns:
            AuditLog: The created audit log entry
        """
        # Extract request data if provided
        request_method = None
        request_path = None
        request_data = None
        ip_address = None
        user_agent = None
        
        if request:
            request_method = request.method
            request_path = request.path
            if hasattr(request, 'data'):
                # Clone and sanitize request data (e.g., remove sensitive fields)
                request_data = cls._sanitize_data(request.data)
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT')
        
        # Extract company data
        company_id = None
        company_name = None
        
        if company:
            company_id = str(company.id)
            company_name = company.name
        elif user and not user.is_anonymous and hasattr(user, 'company') and user.company:
            company_id = str(user.company.id)
            company_name = user.company.name
        
        # Handle username for anonymous users
        username = None
        actual_user = None
        
        if user and not user.is_anonymous:
            username = user.username
            actual_user = user
        elif user and user.is_anonymous:
            username = 'anonymous'
            actual_user = None
        
        # Create the audit log entry
        return cls.objects.create(
            user=actual_user,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            entity_name=entity_name,
            company_id=company_id,
            company_name=company_name,
            request_method=request_method,
            request_path=request_path,
            request_data=request_data,
            response_status=response_status,
            additional_data=additional_data
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _sanitize_data(data):
        """Remove sensitive information from request data"""
        if not data:
            return {}
            
        # Create a copy of the data
        sanitized = dict(data)
        
        # Remove sensitive fields
        sensitive_fields = ['password', 'token', 'secret', 'key', 'auth', 'credential']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '********'
                
        return sanitized 