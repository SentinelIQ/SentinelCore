from rest_framework import status
from django.contrib.auth import get_user_model
from api.core.viewsets import CreateModelMixin

User = get_user_model()


class UserCreateMixin(CreateModelMixin):
    """
    Mixin for user creation operations.
    """
    success_message_create = "User created successfully"

    def perform_create(self, serializer):
        """
        Set company based on the creating user (unless they're a superuser)
        """
        user = self.request.user
        
        # If a superuser is creating the user, use the company from the request
        if user.is_superuser:
            return serializer.save()
        # If a company admin is creating a user, force the company to be their own
        elif user.is_admin_company:
            return serializer.save(company=user.company) 