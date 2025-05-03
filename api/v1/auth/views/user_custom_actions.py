from rest_framework import status
from rest_framework.decorators import action
from api.core.responses import success_response
import logging

logger = logging.getLogger(__name__)


class UserCustomActionsMixin:
    """
    Mixin for user custom actions like profile retrieval.
    """
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get the current user's profile.
        
        Returns:
            The serialized user data of the authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return success_response(
            data=serializer.data,
            message="Profile retrieved successfully"
        ) 