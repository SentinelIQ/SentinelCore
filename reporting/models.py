from django.db import models
from api.core.models import CoreModel

# Create your models here.

class BaseReport(CoreModel):
    """
    Abstract base class for report models.
    Extend this if persistent report storage is needed in the future.
    Currently, reports are generated on-demand without persistence.
    """
    class Meta:
        abstract = True
