import logging
from rest_framework import status
from rest_framework.response import Response
from incidents.models import Incident
from alerts.models import Alert

logger = logging.getLogger('api.incidents')


class IncidentCreateMixin:
    """
    Mixin para operações de criação de incidente
    """
    def perform_create(self, serializer):
        """
        Cria um incidente, atribuindo automaticamente o usuário e empresa.
        """
        user = self.request.user
        
        # Cria o incidente
        instance = serializer.save(
            created_by=user,
            company=user.company
        )
        
        # Log da criação do incidente
        logger.info(f"Incidente criado: {instance.title} ({instance.severity}) por {user.username}")
        
        # Verifica se houve alertas relacionados
        alerts_count = instance.related_alerts.count()
        if alerts_count > 0:
            logger.info(f"Incidente {instance.id} vinculado a {alerts_count} alertas") 