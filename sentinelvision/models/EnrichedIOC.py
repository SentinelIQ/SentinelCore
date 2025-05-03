from django.db import models
from django.utils import timezone
from api.core.models import CoreModel

class EnrichmentStatusEnum(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ENRICHED = 'enriched', 'Enriched'
    NOT_FOUND = 'not_found', 'Not Found'

class IOCTypeEnum(models.TextChoices):
    IP = 'ip', 'IP Address'
    DOMAIN = 'domain', 'Domain'
    URL = 'url', 'URL'
    HASH_MD5 = 'md5', 'MD5 Hash'
    HASH_SHA1 = 'sha1', 'SHA1 Hash'
    HASH_SHA256 = 'sha256', 'SHA256 Hash'
    EMAIL = 'email', 'Email Address'
    CVE = 'cve', 'CVE'
    FILENAME = 'filename', 'Filename'
    FILEPATH = 'filepath', 'Filepath'
    REGISTRY = 'registry', 'Registry Key'
    OTHER = 'other', 'Other'

class TLPLevelEnum(models.TextChoices):
    WHITE = 'white', 'TLP:WHITE'
    GREEN = 'green', 'TLP:GREEN'
    AMBER = 'amber', 'TLP:AMBER'
    RED = 'red', 'TLP:RED'

class EnrichedIOC(CoreModel):
    """
    Store enriched IOC data per tenant.
    Maintains an index of IOCs with their enrichment status, source feeds,
    and metadata for each tenant.
    """
    # Tenant/Company Scope
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='enriched_iocs',
        verbose_name='Company'
    )
    
    # IOC Identification
    ioc_type = models.CharField(
        'IOC Type', 
        max_length=20,
        choices=IOCTypeEnum.choices
    )
    value = models.TextField('IOC Value')
    
    # Enrichment Status
    status = models.CharField(
        'Enrichment Status',
        max_length=20,
        choices=EnrichmentStatusEnum.choices,
        default=EnrichmentStatusEnum.PENDING
    )
    first_seen = models.DateTimeField(
        'First Seen',
        default=timezone.now
    )
    last_checked = models.DateTimeField(
        'Last Checked',
        default=timezone.now
    )
    last_matched = models.DateTimeField(
        'Last Matched',
        null=True,
        blank=True
    )
    
    # Metadata
    source = models.CharField(
        'Source',
        max_length=100,
        default='manual',
        help_text='Original source of the IOC (alert, feed, manual)'
    )
    description = models.TextField(
        'Description',
        blank=True
    )
    tlp = models.CharField(
        'TLP',
        max_length=10,
        choices=TLPLevelEnum.choices,
        default=TLPLevelEnum.AMBER
    )
    confidence = models.FloatField(
        'Confidence',
        default=0.0
    )
    
    # Relationships with Matching Feeds
    matched_feeds = models.ManyToManyField(
        'sentinelvision.FeedModule',
        through='IOCFeedMatch',
        related_name='matched_iocs',
        verbose_name='Matched Feeds'
    )
    
    # Tag storage as JSON field
    tags = models.JSONField(
        'Tags',
        default=list,
        blank=True,
        help_text='Tags associated with this IOC'
    )
    
    # Elasticsearch index data - this should match with ES document ID
    es_index = models.CharField(
        'Elasticsearch Index',
        max_length=100,
        blank=True,
        help_text='Name of the Elasticsearch index where this IOC is stored'
    )
    es_doc_id = models.CharField(
        'Elasticsearch Document ID',
        max_length=100,
        blank=True,
        help_text='ID of the document in Elasticsearch'
    )
    
    class Meta:
        verbose_name = 'Enriched IOC'
        verbose_name_plural = 'Enriched IOCs'
        ordering = ['-last_checked']
        # Ensure uniqueness per tenant and IOC
        unique_together = [['company', 'ioc_type', 'value']]
        indexes = [
            models.Index(fields=['company', 'ioc_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['value']),
            models.Index(fields=['last_checked']),
            models.Index(fields=['status', 'last_checked']),
        ]
    
    def __str__(self):
        return f"{self.get_ioc_type_display()}: {self.value} ({self.company.name})"
    
    def mark_checked(self):
        """Mark the IOC as checked."""
        self.last_checked = timezone.now()
        self.save(update_fields=['last_checked'])
    
    def mark_enriched(self, confidence=None, matched_feeds=None, tags=None):
        """
        Mark the IOC as enriched with matches.
        
        Args:
            confidence (float): New confidence score
            matched_feeds (list): List of feed IDs that matched
            tags (list): List of tags from matching feeds
        """
        self.status = EnrichmentStatusEnum.ENRICHED
        self.last_checked = timezone.now()
        self.last_matched = timezone.now()
        
        if confidence is not None:
            self.confidence = confidence
        
        if tags:
            # Merge with existing tags, remove duplicates
            existing_tags = set(self.tags)
            new_tags = existing_tags.union(set(tags))
            self.tags = list(new_tags)
        
        self.save()
        
        # Update matched feeds if provided
        if matched_feeds:
            for feed_id in matched_feeds:
                IOCFeedMatch.objects.get_or_create(
                    ioc=self,
                    feed_id=feed_id,
                    defaults={
                        'match_time': timezone.now()
                    }
                )
    
    def mark_not_found(self):
        """Mark the IOC as not found in any feeds."""
        self.status = EnrichmentStatusEnum.NOT_FOUND
        self.last_checked = timezone.now()
        self.save(update_fields=['status', 'last_checked'])
    
    @property
    def match_count(self):
        """Get the number of feeds that matched this IOC."""
        return self.matched_feeds.count()
    
    @property
    def is_pending(self):
        """Check if the IOC is pending enrichment."""
        return self.status == EnrichmentStatusEnum.PENDING
    
    @property
    def is_enriched(self):
        """Check if the IOC has been enriched."""
        return self.status == EnrichmentStatusEnum.ENRICHED
    
    @property
    def elasticsearch_id(self):
        """Generate the Elasticsearch document ID for this IOC."""
        return f"{self.company.id}_{self.ioc_type}_{self.value}"
    
    def get_index_name(self):
        """Get the Elasticsearch index name for this IOC."""
        return f"tenant_{self.company.id}_enriched_iocs"


class IOCFeedMatch(models.Model):
    """
    Track matches between IOCs and feeds.
    This table serves as a many-to-many relationship with additional match metadata.
    """
    ioc = models.ForeignKey(
        EnrichedIOC,
        on_delete=models.CASCADE,
        related_name='feed_matches',
        verbose_name='IOC'
    )
    feed = models.ForeignKey(
        'sentinelvision.FeedModule',
        on_delete=models.CASCADE,
        related_name='ioc_matches',
        verbose_name='Feed'
    )
    match_time = models.DateTimeField(
        'Match Time',
        default=timezone.now
    )
    feed_confidence = models.FloatField(
        'Feed Confidence',
        default=0.0
    )
    feed_tags = models.JSONField(
        'Feed Tags',
        default=list,
        blank=True
    )
    metadata = models.JSONField(
        'Metadata',
        default=dict,
        blank=True,
        help_text='Additional metadata about the match'
    )
    
    class Meta:
        verbose_name = 'IOC-Feed Match'
        verbose_name_plural = 'IOC-Feed Matches'
        ordering = ['-match_time']
        # Ensure uniqueness of matches
        unique_together = [['ioc', 'feed']]
        indexes = [
            models.Index(fields=['ioc', 'feed']),
            models.Index(fields=['match_time']),
        ]
    
    def __str__(self):
        return f"{self.ioc} → {self.feed.name}" 