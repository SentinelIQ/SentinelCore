from django.db import models
import uuid
from django.utils.text import slugify
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model
from companies.models import Company
from django.core.exceptions import ValidationError
from django.utils import timezone
from api.v1.wiki.enums import ArticleVisibilityEnum
from api.core.utils.enum_utils import enum_to_choices
from api.core.models import CoreModel

User = get_user_model()


class KnowledgeCategory(CoreModel):
    """
    Categories for knowledge articles.
    """
    name = models.CharField('Name', max_length=100)
    slug = models.SlugField('Slug', max_length=120, unique=True)
    description = models.TextField('Description', blank=True, null=True)
    
    # Optional parent for hierarchical categories
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Parent Category'
    )
    
    # For multi-tenant isolation
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='knowledge_categories',
        verbose_name='Company',
        null=True,
        blank=True,
        help_text='If null, this is a global category visible to all companies'
    )
    
    class Meta:
        verbose_name = 'Knowledge Category'
        verbose_name_plural = 'Knowledge Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['company', 'slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class KnowledgeArticle(CoreModel):
    """
    Knowledge article model for the internal wiki.
    """
    title = models.CharField('Title', max_length=200)
    slug = models.SlugField('Slug', max_length=250, unique=True)
    content = models.TextField('Content')
    
    # Visibility scope
    visibility = models.CharField(
        'Visibility',
        max_length=20,
        choices=enum_to_choices(ArticleVisibilityEnum),
        default=ArticleVisibilityEnum.PRIVATE.value
    )
    
    # Categorization
    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='Category'
    )
    
    tags = ArrayField(
        models.CharField(max_length=50),
        verbose_name='Tags',
        blank=True,
        default=list
    )
    
    # Relationships
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='knowledge_articles',
        verbose_name='Company',
        null=True,
        blank=True,
        help_text='If null, this is a global article visible to all companies'
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='authored_articles',
        verbose_name='Author'
    )
    
    # Optional publish/expiry dates
    published_at = models.DateTimeField('Published at', null=True, blank=True)
    expires_at = models.DateTimeField('Expires at', null=True, blank=True)
    
    # Fields for article quality tracking
    is_reviewed = models.BooleanField('Reviewed', default=False)
    version = models.PositiveIntegerField('Version', default=1)
    last_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_articles',
        verbose_name='Last Reviewed By'
    )
    
    class Meta:
        verbose_name = 'Knowledge Article'
        verbose_name_plural = 'Knowledge Articles'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['company', 'visibility']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """
        Validate model constraints.
        """
        super().clean()
        
        # If visibility is PUBLIC, company must be None
        if self.visibility == ArticleVisibilityEnum.PUBLIC.value and self.company is not None:
            raise ValidationError({
                'visibility': 'Public articles cannot be associated with a company.'
            })
        
        # If visibility is PRIVATE, company must be set
        if self.visibility == ArticleVisibilityEnum.PRIVATE.value and self.company is None:
            raise ValidationError({
                'company': 'Private articles must be associated with a company.'
            })
        
        # Ensure consistency between article company and category company
        if self.category and self.category.company and self.company and self.category.company != self.company:
            raise ValidationError({
                'category': 'The category must belong to the same company as the article.'
            })
    
    def save(self, *args, **kwargs):
        """
        Override save method to generate slug and handle publishing.
        """
        # Generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure slug uniqueness
            base_slug = self.slug
            counter = 1
            while KnowledgeArticle.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Set published_at date if not set
        if not self.published_at:
            self.published_at = timezone.now()
            
        # Run validation
        self.full_clean()
            
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """
        Check if the article is expired.
        """
        if self.expires_at:
            return self.expires_at < timezone.now()
        return False
    
    @property
    def is_published(self):
        """
        Check if the article is published.
        """
        now = timezone.now()
        if self.published_at:
            if self.expires_at:
                return self.published_at <= now < self.expires_at
            return self.published_at <= now
        return False
