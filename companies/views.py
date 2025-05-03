"""
This file is a redirection layer to maintain backward compatibility.
All new code should use the views from api/v1/companies/views.
"""
from api.v1.companies.views import CompanyViewSet

__all__ = ['CompanyViewSet']
