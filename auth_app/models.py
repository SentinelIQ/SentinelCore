from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from api.v1.auth.enums import UserRoleEnum
from api.core.utils.enum_utils import enum_to_choices


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=enum_to_choices(UserRoleEnum),
        default=UserRoleEnum.ANALYST_COMPANY.value,
    )
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='users'
    )
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username
    
    @property
    def is_admin_company(self):
        return self.role == UserRoleEnum.ADMIN_COMPANY.value
    
    @property
    def is_analyst_company(self):
        return self.role == UserRoleEnum.ANALYST_COMPANY.value
    
    @property
    def is_read_only(self):
        return self.role == UserRoleEnum.READ_ONLY.value
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = UserRoleEnum.SUPERUSER.value
            self.company = None
        super().save(*args, **kwargs)
