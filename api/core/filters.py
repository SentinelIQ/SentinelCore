from django.contrib.postgres.fields import ArrayField
from django_filters import Filter
from django_filters.constants import EMPTY_VALUES
from django.forms import CharField
from rest_framework import filters


class ArrayFieldFilter(Filter):
    """
    Custom filter for ArrayField from django.contrib.postgres.fields.
    
    This filter allows filtering by values contained in an ArrayField.
    """
    field_class = CharField

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'contains')
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        
        # If exact, search for arrays that contain exactly this value
        if self.lookup_expr == 'exact':
            lookup = '%s__contains' % self.field_name
            return qs.filter(**{lookup: [value]})
        
        # Search for arrays that contain this value
        lookup = '%s__%s' % (self.field_name, self.lookup_expr)
        return qs.filter(**{lookup: value})


def get_array_field_filter_overrides():
    """
    Returns a dictionary of filter overrides for ArrayField.
    
    Use this in Meta.filter_overrides of your FilterSet classes:
    
    class Meta:
        model = YourModel
        fields = ['field1', 'field2', 'array_field']
        filter_overrides = get_array_field_filter_overrides()
    """
    return {
        ArrayField: {
            'filter_class': ArrayFieldFilter,
            'extra': lambda f: {
                'lookup_expr': 'contains',
            }
        }
    } 