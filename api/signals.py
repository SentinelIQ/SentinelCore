"""
Django signals module for the API application.

This module contains all the signal handlers for the API application,
including authentication signals, model signals, etc.
"""

import logging
from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.signals import user_login_failed
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger('api.auth')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log when a user logs in.
    
    Args:
        sender: The model class that sent the signal
        request: The request object
        user: The user that just logged in
        kwargs: Additional arguments
    """
    logger.info(f"User {user.username} logged in")
    
    # Add more custom logic for login tracking if needed


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log when a user logs out.
    
    Args:
        sender: The model class that sent the signal
        request: The request object
        user: The user that just logged out
        kwargs: Additional arguments
    """
    if user:
        logger.info(f"User {user.username} logged out")
    else:
        logger.info("Anonymous user logged out")
    
    # Add more custom logic for logout tracking if needed


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Log when a user login fails.
    
    Args:
        sender: The model class that sent the signal
        credentials: The credentials that were used to attempt login
        request: The request object
        kwargs: Additional arguments
    """
    # Get username from credentials, but don't log the password
    username = credentials.get('username', 'unknown')
    
    logger.warning(f"Login failed for username: {username}")
    
    # Add more custom logic for failed login tracking if needed
    # E.g., tracking failed login attempts for brute force detection 