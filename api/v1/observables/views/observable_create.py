from django.db import IntegrityError, transaction
import logging
from observables.models import Observable

logger = logging.getLogger('api.observables')


class ObservableCreateViewMixin:
    """
    Mixin for Observable creation operations.
    """
    def perform_create(self, serializer):
        """
        Creates an observable, automatically assigning the user and company.
        Handles duplicate entries gracefully.
        """
        user = self.request.user
        
        # First check if a duplicate exists
        try:
            existing = Observable.objects.get(
                type=serializer.validated_data['type'],
                value=serializer.validated_data['value'],
                company=user.company
            )
            # If we found a duplicate without error, return it
            logger.warning(f"Duplicate observable found: {existing.type}:{existing.value}")
            return existing
        except Observable.DoesNotExist:
            # If no duplicate exists, create a new observable
            try:
                with transaction.atomic():
                    obs = serializer.save(created_by=user, company=user.company)
                logger.info(f"Observable created: {obs.type}:{obs.value} by {user.username}")
                return obs
            except IntegrityError as e:
                # If there's a race condition and another duplicate was created
                logger.error(f"Error creating observable: {str(e)}")
                raise 