import os
import logging
import subprocess
import sys
from celery import shared_task
from celery.utils.log import get_task_logger

# Use the Celery-specific task logger
logger = get_task_logger(__name__)

@shared_task(
    name="api.core.tasks.run_migrations",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True,
    queue='sentineliq_soar_setup'  # Updated queue name
)
def run_migrations(self):
    """
    Task to run makemigrations and migrate automatically on system startup.
    This ensures the database is always in sync with the models.
    
    Features:
    - Auto-retry on failure (up to 3 times)
    - Late acknowledgment (only ack if task completes)
    - Detailed logging
    - Safe subprocess execution
    """
    task_id = self.request.id
    logger.info(f"Starting run_migrations task with ID: {task_id}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    try:
        # Run makemigrations
        logger.info("Executing makemigrations...")
        makemigrations_result = subprocess.run(
            ["python", "manage.py", "makemigrations", "--noinput"], 
            capture_output=True, 
            text=True,
            check=True
        )
        logger.info(f"makemigrations output: {makemigrations_result.stdout}")
        
        # Check if any migrations were created
        if "No changes detected" in makemigrations_result.stdout:
            logger.info("No model changes detected that require migrations")
        else:
            logger.info("New migrations created successfully")
        
        # Run migrate
        logger.info("Executing migrate...")
        migrate_result = subprocess.run(
            ["python", "manage.py", "migrate", "--noinput"], 
            capture_output=True, 
            text=True,
            check=True
        )
        logger.info(f"migrate output: {migrate_result.stdout}")
        logger.info(f"Migrations completed successfully for task {task_id}")
        
        return {
            "status": "success",
            "task_id": self.request.id,
            "makemigrations": makemigrations_result.stdout,
            "migrate": migrate_result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        error_message = f"Error in migration process: {e.stderr}"
        logger.error(error_message)
        # Raise exception to trigger retry mechanism
        raise Exception(f"Migration command failed: {error_message}")
        
    except Exception as e:
        error_message = f"Unexpected error during migration process: {str(e)}"
        logger.error(error_message)
        logger.exception(e)  # Log full traceback
        # Raise exception to trigger retry mechanism 
        raise 