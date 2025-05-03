from rest_framework import status
from django.contrib.auth import get_user_model
from api.core.viewsets import RetrieveModelMixin, ListModelMixin

User = get_user_model()


class UserDetailMixin(ListModelMixin, RetrieveModelMixin):
    """
    Mixin for user detail operations (retrieve and list).
    """
    
    def get_queryset(self):
        """
        Filter users based on user's permissions:
        - Superuser can see all users
        - Company admin can see users of their company
        - Company analyst can only see themselves
        """
        user = self.request.user
        queryset = User.objects.all()
        
        if user.is_superuser:
            return queryset
        elif user.is_admin_company:
            return queryset.filter(company=user.company)
        else:
            return queryset.filter(id=user.id) 