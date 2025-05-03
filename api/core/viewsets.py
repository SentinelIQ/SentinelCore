from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from django.db import transaction
from .responses import success_response, created_response, no_content_response, error_response


class CreateModelMixin(mixins.CreateModelMixin):
    """
    Enhanced Create mixin that uses standardized response format.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            instance = self.perform_create(serializer)
        
        # Allow serializer override for response
        if hasattr(serializer, 'get_response_serializer'):
            response_serializer = serializer.get_response_serializer(instance)
            response_data = response_serializer.data
        else:
            response_data = serializer.data
            
        # Custom headers from original implementation
        headers = self.get_success_headers(serializer.data)
        
        # Get custom message if provided by the viewset
        message = getattr(self, 'success_message_create', "Resource created successfully")
        
        return created_response(
            data=response_data, 
            message=message, 
            headers=headers
        )
    
    def perform_create(self, serializer):
        """
        Modified to return the created instance.
        """
        return serializer.save()


class ListModelMixin(mixins.ListModelMixin):
    """
    Enhanced List mixin that uses standardized response format.
    """
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class RetrieveModelMixin(mixins.RetrieveModelMixin):
    """
    Enhanced Retrieve mixin that uses standardized response format.
    """
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)


class UpdateModelMixin(mixins.UpdateModelMixin):
    """
    Enhanced Update mixin that uses standardized response format.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            instance = self.perform_update(serializer)
            
        # If object has changed, get fresh copy
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
            
        # Get response data
        if hasattr(serializer, 'get_response_serializer'):
            response_serializer = serializer.get_response_serializer(instance)
            response_data = response_serializer.data
        else:
            response_data = serializer.data
            
        # Get custom message
        message = getattr(self, 'success_message_update', "Resource updated successfully")
            
        return success_response(data=response_data, message=message)
    
    def perform_update(self, serializer):
        """
        Modified to return the updated instance.
        """
        return serializer.save()


class DestroyModelMixin(mixins.DestroyModelMixin):
    """
    Enhanced Destroy mixin that uses standardized response format.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            self.perform_destroy(instance)
            
        # Get custom message
        message = getattr(self, 'success_message_delete', "Resource deleted successfully")
            
        return no_content_response()


class StandardViewSet(CreateModelMixin,
                     ListModelMixin,
                     RetrieveModelMixin,
                     UpdateModelMixin,
                     DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    A viewset that provides standard create, list, retrieve, update, and destroy actions
    with consistent response formatting.
    """
    pass


class ReadOnlyViewSet(ListModelMixin,
                     RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """
    A viewset that provides only list and retrieve actions
    with consistent response formatting.
    """
    pass 