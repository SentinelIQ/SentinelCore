import logging
from celery import shared_task
from django.conf import settings
from mitre.services import MitreImporter

logger = logging.getLogger(__name__)


@shared_task(name="mitre.tasks.sync_mitre_data")
def sync_mitre_data():
    """
    Celery task that synchronizes MITRE ATT&CK framework data with local database.
    This task runs every 10 minutes as scheduled by Celery Beat.
    It only performs a quick update on new or changed data.
    """
    logger.info("Starting scheduled MITRE ATT&CK sync task")
    
    try:
        importer = MitreImporter()
        result = importer.run_full_sync(
            source_type="json",
            force=False  # Don't force a full reimport, only update
        )
        
        logger.info(f"Scheduled MITRE ATT&CK sync completed: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error during scheduled MITRE ATT&CK sync: {str(e)}")
        raise 