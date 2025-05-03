from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AdminRateThrottle(UserRateThrottle):
    """
    Throttling adaptativo baseado no perfil do usuário.
    """
    scope = 'admin'
    rate = '120/minute'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                # Rate limit mais alto para superusuários
                self.rate = '200/minute'
            elif request.user.is_admin_company:
                # Rate limit médio para admins de empresa
                self.rate = '120/minute'
            else:
                # Rate limit padrão para analistas
                self.rate = '60/minute'
        return super().get_cache_key(request, view)


class StandardUserRateThrottle(UserRateThrottle):
    """
    Throttling para usuários regulares.
    """
    scope = 'user'
    rate = '60/minute'


class PublicEndpointRateThrottle(AnonRateThrottle):
    """
    Throttling para endpoints públicos.
    """
    scope = 'public'
    rate = '30/minute'


class SensitiveEndpointRateThrottle(UserRateThrottle):
    """
    Throttling mais rigoroso para endpoints sensíveis como autenticação.
    """
    scope = 'sensitive'
    rate = '5/minute' 