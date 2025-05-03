from django.db import models
from django.utils.translation import gettext_lazy as _
from api.core.models import CoreModel


class Company(CoreModel):
    name = models.CharField(_('name'), max_length=255, unique=True)
    
    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')
        ordering = ['name']
    
    def __str__(self):
        return self.name
