"""
MITRE ATT&CK framework synchronization tasks.

This module defines background tasks for synchronizing and managing
MITRE ATT&CK framework data.
"""

import logging
from sentineliq.tasks.base import register_task, BaseTask

# Configure logger
logger = logging.getLogger('sentineliq.tasks.mitre')


@register_task(
    name='sentineliq.tasks.mitre.sync_mitre_data',
    queue='sentineliq_soar_setup',
    base=BaseTask
)
def sync_mitre_data(self):
    """
    Synchronize MITRE ATT&CK framework data with local database.
    
    This task retrieves the latest MITRE ATT&CK framework data
    and updates the local database with any changes.
    
    Returns:
        dict: Synchronization results
    """
    from mitre.services import MitreImporter
    
    logger.info("Starting MITRE ATT&CK sync task")
    
    try:
        importer = MitreImporter()
        result = importer.run_full_sync(
            source_type="json",
            force=False  # Don't force a full reimport, only update
        )
        
        logger.info(f"MITRE ATT&CK sync completed: {result}")
        return {
            'status': 'success',
            'result': result
        }
    except Exception as e:
        logger.exception(f"Error during MITRE ATT&CK sync: {str(e)}")
        
        return {
            'status': 'error',
            'error': str(e)
        } 