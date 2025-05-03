import logging
from rest_framework import status
from api.core.responses import created_response
from alerts.models import Alert
from companies.models import Company
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('api.alerts')


class AlertCreateMixin:
    """
    Mixin for alert creation operations
    """
    def perform_create(self, serializer):
        """
        Creates an alert, automatically assigning the user and company.
        
        For users with a company, their company is automatically assigned.
        For superusers without a company, a company_id must be provided in the request data.
        """
        user = self.request.user
        
        # Only continue with user's company if it exists
        if user.company:
            # User has a company assigned, use it
            instance = serializer.save(created_by=user, company=user.company)
            logger.info(f"Alert created for company {user.company.name} by {user.username}")
        else:
            # For users without company (like superusers), get company from request data
            company_id = self.request.data.get('company')
            logger.info(f"User without company, company_id from request: {company_id}")
            
            if not company_id:
                # Company is required for alerts
                logger.warning("No company_id found in request data")
                raise ValidationError({
                    "company": "Company ID is required when creating an alert as a superuser or user without company"
                })
            
            try:
                company = Company.objects.get(id=company_id)
                logger.info(f"Found company with id {company_id}: {company.name}")
                instance = serializer.save(created_by=user, company=company)
            except Company.DoesNotExist:
                logger.warning(f"Company with id {company_id} not found")
                raise ValidationError({"company": f"Company with id {company_id} does not exist"})
        
        logger.info(f"Alert created: {instance.title} ({instance.severity}) by {user.username}") 