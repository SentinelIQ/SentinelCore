import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """
    Filter set for the User model.
    
    Allows filtering users by various criteria such as:
    - Username
    - Email
    - First and last name
    - Company
    - User type (is_superuser, is_admin_company, is_analyst_company)
    - Date joined
    """
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date ranges
    date_joined_after = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_before = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='lte')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter()
    is_superuser = django_filters.BooleanFilter()
    is_admin_company = django_filters.BooleanFilter()
    is_analyst_company = django_filters.BooleanFilter()
    
    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'company',
            'is_active',
            'is_superuser',
            'is_admin_company',
            'is_analyst_company',
        ] 