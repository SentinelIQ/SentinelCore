import os
import logging
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    """
    Create a superuser after the initial migration.
    """
    if sender.name == 'auth_app':
        username = os.getenv('ADMIN_USERNAME', 'adminsentinel')
        email = os.getenv('ADMIN_EMAIL', 'admin@sentineliq.com')
        password = os.getenv('ADMIN_PASSWORD', 'changeme123!')
        
        try:
            # Check if the superuser already exists
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                logger.info(f"Superuser '{username}' created successfully.")
            else:
                logger.info(f"Superuser '{username}' already exists.")
        except Exception as e:
            logger.error(f"Error creating superuser: {str(e)}") 