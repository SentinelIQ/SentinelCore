from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings
from .responses import standard_response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with configurable page size.
    
    Includes standardized response formatting with metadata for pagination details.
    """
    page_size = getattr(settings, 'PAGE_SIZE', 50)
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
    def get_paginated_response(self, data):
        """
        Return a standardized response format with pagination metadata.
        """
        return Response(standard_response(
            data={'results': data},  # Wrap data in 'results' key for test compatibility
            metadata={
                'pagination': {
                    'count': self.page.paginator.count,
                    'page': self.page.number,
                    'pages': self.page.paginator.num_pages,
                    'page_size': self.get_page_size(self.request),
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link()
                }
            }
        ))


class LargeResultsSetPagination(StandardResultsSetPagination):
    """
    Pagination for large result sets.
    """
    page_size = 100
    max_page_size = 1000


class SmallResultsSetPagination(StandardResultsSetPagination):
    """
    Pagination for small result sets.
    """
    page_size = 10
    max_page_size = 100
    

class CustomPageSizePagination(StandardResultsSetPagination):
    """
    Pagination with custom page size via query parameter.
    """
    def get_page_size(self, request):
        """
        Get page size from request query parameter or use default.
        """
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
                return min(page_size, self.max_page_size)
            except (ValueError, TypeError):
                pass
        
        return self.page_size 