"""
Standard enums for the wiki module.
These enums are used across models, serializers, and views to ensure consistency
and proper documentation in OpenAPI schemas.

Usage examples:

In models:
```python
from api.v1.wiki.enums import ArticleVisibilityEnum
from api.core.utils.enum_utils import enum_to_choices

visibility = models.CharField(
    max_length=20,
    choices=enum_to_choices(ArticleVisibilityEnum),
    default=ArticleVisibilityEnum.PRIVATE.value
)
```

In serializers:
```python
from api.v1.wiki.enums import ArticleVisibilityEnum
from api.core.utils.enum_utils import enum_to_choices

visibility = serializers.ChoiceField(
    choices=enum_to_choices(ArticleVisibilityEnum),
    default=ArticleVisibilityEnum.PRIVATE.value
)
```

In views/viewsets:
```python
from api.v1.wiki.enums import ArticleVisibilityEnum
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='visibility',
            description='Filter by article visibility',
            enum=ArticleVisibilityEnum,
            required=False
        )
    ]
)
def list(self, request):
    # View implementation
    pass
```
"""
from enum import Enum


class ArticleVisibilityEnum(str, Enum):
    """Wiki article visibility options"""
    PUBLIC = "public"  # Public (All Companies)
    PRIVATE = "private"  # Private (Single Company) 