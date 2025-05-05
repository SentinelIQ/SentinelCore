"""
Central module for registering models in the audit system.

This module provides functions to automatically register models
in the django-auditlog audit system.
"""

import logging
from auditlog.registry import auditlog
from django.apps import apps

logger = logging.getLogger('auditlog')

# List of models that should be excluded from automatic auditing
DEFAULT_EXCLUDE_MODELS = [
    'django.contrib.auth.models.Permission',
    'django.contrib.auth.models.Group',
    'django.contrib.admin.models.LogEntry',
    'django.contrib.sessions.models.Session',
    'django.contrib.contenttypes.models.ContentType',
]

# Models that need fields excluded from auditing
EXCLUDE_FIELDS_MAP = {
    'auth_app.models.User': ['password', 'last_login'],
    'auth_app.models.Token': ['key'],
}


def get_model(app_label, model_name):
    """
    Helper function to get model class from app_label and model_name.
    
    Args:
        app_label: The Django app label
        model_name: The model name
        
    Returns:
        Model class or None if not found
    """
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        logger.warning(f"Model {app_label}.{model_name} not found")
        return None


def register_auth_models():
    """
    Register auth related models for auditing.
    
    This will register User model and related models for audit tracking.
    """
    try:
        # Import models individually to avoid triggering AppConfig.ready()
        User = get_model('auth_app', 'User')
        Token = get_model('auth_app', 'Token')
        
        if User:
            auditlog.register(User, exclude=['password', 'last_login'])
            logger.info(f"Registered User model for auditing")
        
        if Token:
            auditlog.register(Token, exclude=['key'])
            logger.info(f"Registered Token model for auditing")
            
    except Exception as e:
        logger.error(f"Error registering auth models for auditing: {str(e)}")


def register_alert_models():
    """
    Register Alert related models for auditing.
    
    This will register Alert model and related models for audit tracking.
    """
    try:
        # Import models
        Alert = get_model('alerts', 'Alert')
        AlertComment = get_model('alerts', 'AlertComment')
        AlertAttachment = get_model('alerts', 'AlertAttachment')
        AlertTag = get_model('alerts', 'AlertTag')
        AlertRule = get_model('alerts', 'AlertRule')
        
        # Register Alert model
        if Alert:
            auditlog.register(Alert)
            logger.info(f"Registered Alert model for auditing")
            
        # Register AlertComment model
        if AlertComment:
            auditlog.register(AlertComment)
            logger.info(f"Registered AlertComment model for auditing")
            
        # Register AlertAttachment model
        if AlertAttachment:
            auditlog.register(AlertAttachment)
            logger.info(f"Registered AlertAttachment model for auditing")
            
        # Register AlertTag model
        if AlertTag:
            auditlog.register(AlertTag)
            logger.info(f"Registered AlertTag model for auditing")
            
        # Register AlertRule model
        if AlertRule:
            auditlog.register(AlertRule)
            logger.info(f"Registered AlertRule model for auditing")
            
    except Exception as e:
        logger.error(f"Error registering alert models for auditing: {str(e)}")


def register_incident_models():
    """
    Register Incident related models for auditing.
    
    This will register Incident model and related models for audit tracking.
    """
    try:
        # Import models
        Incident = get_model('incidents', 'Incident')
        IncidentTask = get_model('incidents', 'IncidentTask')
        IncidentObservable = get_model('incidents', 'IncidentObservable')
        TimelineEvent = get_model('incidents', 'TimelineEvent')
        
        # Register Incident model
        if Incident:
            auditlog.register(Incident)
            logger.info(f"Registered Incident model for auditing")
            
        # Register IncidentTask model
        if IncidentTask:
            auditlog.register(IncidentTask)
            logger.info(f"Registered IncidentTask model for auditing")
            
        # Register IncidentObservable model
        if IncidentObservable:
            auditlog.register(IncidentObservable)
            logger.info(f"Registered IncidentObservable model for auditing")
            
        # Register TimelineEvent model
        if TimelineEvent:
            auditlog.register(TimelineEvent)
            logger.info(f"Registered TimelineEvent model for auditing")
            
    except Exception as e:
        logger.error(f"Error registering incident models for auditing: {str(e)}")


def register_observable_models():
    """
    Register Observable related models for auditing.
    
    This will register Observable model and related models for audit tracking.
    """
    try:
        # Import models
        Observable = get_model('observables', 'Observable')
        ObservableEnrichment = get_model('observables', 'ObservableEnrichment')
        ExecutionRecord = get_model('observables', 'ExecutionRecord')
        
        # Register Observable model
        if Observable:
            auditlog.register(Observable)
            logger.info(f"Registered Observable model for auditing")
            
        # Register ObservableEnrichment model
        if ObservableEnrichment:
            auditlog.register(ObservableEnrichment)
            logger.info(f"Registered ObservableEnrichment model for auditing")
            
        # Register ExecutionRecord model
        if ExecutionRecord:
            auditlog.register(ExecutionRecord)
            logger.info(f"Registered ExecutionRecord model for auditing")
            
    except Exception as e:
        logger.error(f"Error registering observable models for auditing: {str(e)}")


def register_task_models():
    """
    Register Task related models for auditing.
    
    This will register Task model and related models for audit tracking.
    """
    try:
        # Import models
        Task = get_model('tasks', 'Task')
        
        # Register Task model
        if Task:
            auditlog.register(Task)
            logger.info(f"Registered Task model for auditing")
            
    except Exception as e:
        logger.error(f"Error registering task models for auditing: {str(e)}")


def register_company_models():
    """
    Register Company related models for auditing.
    
    This will register Company model and related models for audit tracking.
    """
    try:
        # Import models
        Company = get_model('companies', 'Company')
        
        # Register Company model
        if Company:
            auditlog.register(Company)
            logger.info(f"Registered Company model for auditing")
            
    except Exception as e:
        logger.error(f"Error registering company models for auditing: {str(e)}")


def register_all_models():
    """
    Register all models for auditing.
    
    This is the main entry point for registering all models that should
    be tracked by the audit log system.
    """
    try:
        # Register auth models
        register_auth_models()
        
        # Register alert models
        register_alert_models()
        
        # Register incident models
        register_incident_models()
        
        # Register observable models
        register_observable_models()
        
        # Register task models
        register_task_models()
        
        # Register company models
        register_company_models()
        
        logger.info("All models registered for auditing")
        
    except Exception as e:
        logger.error(f"Error registering models for auditing: {str(e)}")

# Specific registrations for models with custom configurations
def register_auth_models():
    """Registers authentication models with custom configurations."""
    from auth_app.models import User
    auditlog.register(User, exclude_fields=['password', 'last_login', 'user_permissions'])
    logger.info("Authentication models registered for auditing")

def register_company_models():
    """Registers company models with custom configurations."""
    from companies.models import Company
    auditlog.register(Company)
    logger.info("Company models registered for auditing")

def register_alert_models():
    """Registers alert models with custom configurations."""
    from alerts.models import Alert
    auditlog.register(Alert)
    # Try importing AlertObservable model and register it if it exists
    try:
        # This model might not exist yet or has been renamed
        from alerts.models import AlertObservable
        auditlog.register(AlertObservable)
        logger.info("AlertObservable model registered for auditing")
    except ImportError:
        logger.warning("AlertObservable model not found and will not be registered")
    
    logger.info("Alert models registered for auditing")

def register_incident_models():
    """Registers incident models with custom configurations."""
    from incidents.models import Incident, TimelineEvent, IncidentObservable, IncidentTask
    auditlog.register(Incident)
    auditlog.register(TimelineEvent)
    auditlog.register(IncidentObservable)
    auditlog.register(IncidentTask)
    logger.info("Incident models registered for auditing")

def register_observable_models():
    """Registers observable models with custom configurations."""
    from observables.models import Observable, ObservableRelationship
    auditlog.register(Observable)
    auditlog.register(ObservableRelationship)
    logger.info("Observable models registered for auditing")

def register_task_models():
    """Registers task models with custom configurations."""
    from tasks.models import Task
    auditlog.register(Task)
    logger.info("Task models registered for auditing")

def register_sentinelvision_models():
    """Registers SentinelVision models with custom configurations."""
    from sentinelvision.models.FeedModule import FeedModule
    from sentinelvision.models.AnalyzerModule import AnalyzerModule
    from sentinelvision.models.ResponderModule import ResponderModule
    from sentinelvision.models.FeedRegistry import FeedRegistry
    from sentinelvision.models.ExecutionRecord import ExecutionRecord
    from sentinelvision.models.EnrichedIOC import EnrichedIOC, IOCFeedMatch
    
    auditlog.register(FeedModule)
    auditlog.register(AnalyzerModule)
    auditlog.register(ResponderModule)
    auditlog.register(FeedRegistry)
    auditlog.register(ExecutionRecord)
    auditlog.register(EnrichedIOC)
    auditlog.register(IOCFeedMatch)
    logger.info("SentinelVision models registered for auditing")

def register_wiki_models():
    """Registers Wiki models with custom configurations."""
    from wiki.models import KnowledgeArticle, KnowledgeCategory
    auditlog.register(KnowledgeArticle)
    auditlog.register(KnowledgeCategory)
    logger.info("Wiki models registered for auditing")

def register_mitre_models():
    """Registers MITRE models with custom configurations."""
    from mitre.models import MitreTactic, MitreTechnique, MitreMitigation, MitreRelationship
    
    auditlog.register(MitreTactic)
    auditlog.register(MitreTechnique)
    auditlog.register(MitreMitigation)
    auditlog.register(MitreRelationship)
    logger.info("MITRE models registered for auditing")

def register_notification_models():
    """Registers notification models with custom configurations."""
    from notifications.models import NotificationChannel, NotificationRule, Notification
    
    auditlog.register(NotificationChannel, exclude_fields=['api_key', 'webhook_secret'])
    auditlog.register(NotificationRule)
    auditlog.register(Notification)
    logger.info("Notification models registered for auditing")

def register_dashboard_models():
    """Registers dashboard models with custom configurations."""
    from dashboard.models import DashboardPreference
    
    auditlog.register(DashboardPreference)
    logger.info("Dashboard models registered for auditing")

def register_all():
    """Registers all models with custom configurations."""
    register_auth_models()
    register_company_models()
    register_alert_models()
    register_incident_models()
    register_observable_models()
    register_task_models()
    register_sentinelvision_models()
    register_wiki_models()
    register_mitre_models()
    register_notification_models()
    register_dashboard_models()
    logger.info("All models registered for auditing with custom configurations") 