from django.db import models
import uuid


class CoreModel(models.Model):
    """
    Base abstract model for all models in the system.
    Provides common fields like ID, created_at, and updated_at.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True 