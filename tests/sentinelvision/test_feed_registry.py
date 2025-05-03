from django.test import TestCase
from django.utils import timezone
from django.db import transaction, IntegrityError
from datetime import timedelta
from sentinelvision.models import FeedRegistry
from companies.models import Company


class FeedRegistryTest(TestCase):
    """Test suite for the FeedRegistry model"""
    
    def setUp(self):
        # Create test company
        self.company = Company.objects.create(
            name="Test Company"
        )
    
    def test_feed_registry_creation(self):
        """Test creating a feed registry entry"""
        feed = FeedRegistry.objects.create(
            name="Test Feed",
            source_url="https://example.com/feed.csv",
            feed_type="csv",
            company=self.company,
            sync_interval_hours=12
        )
        
        # Check that feed was created
        self.assertEqual(feed.name, "Test Feed")
        self.assertEqual(feed.source_url, "https://example.com/feed.csv")
        self.assertEqual(feed.feed_type, "csv")
        self.assertEqual(feed.company, self.company)
        
        # Check default values
        self.assertTrue(feed.enabled)
        self.assertEqual(feed.sync_status, FeedRegistry.SyncStatus.PENDING)
        self.assertEqual(feed.total_iocs, 0)
        
        # Check that next_sync was set automatically
        self.assertIsNotNone(feed.next_sync)
        
        # Check next_sync is in the future
        self.assertTrue(feed.next_sync > timezone.now())
    
    def test_feed_registry_unique_constraint(self):
        """Test that feed registry entries must be unique per company"""
        # Create a feed
        feed1 = FeedRegistry.objects.create(
            name="First Feed",
            source_url="https://example.com/feed1.csv",
            feed_type="csv",
            company=self.company
        )
        
        # Try to create another feed with same name and source_url for same company
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FeedRegistry.objects.create(
                    name="First Feed",
                    source_url="https://example.com/feed1.csv",
                    feed_type="csv",
                    company=self.company
                )
        
        # Create another company
        company2 = Company.objects.create(
            name="Another Company"
        )
        
        # Should be able to create feed with same name for different company
        feed2 = FeedRegistry.objects.create(
            name="First Feed",
            source_url="https://example.com/feed1.csv",
            feed_type="csv",
            company=company2
        )
        
        self.assertEqual(feed2.name, "First Feed")
        self.assertEqual(feed2.company, company2)
    
    def test_mark_sync_started(self):
        """Test marking a feed as syncing"""
        feed = FeedRegistry.objects.create(
            name="Test Feed",
            source_url="https://example.com/feed.csv",
            feed_type="csv",
            company=self.company
        )
        
        feed.mark_sync_started()
        
        # Refresh from database
        feed.refresh_from_db()
        
        # Check that status was updated
        self.assertEqual(feed.sync_status, FeedRegistry.SyncStatus.SYNCING)
    
    def test_mark_sync_success(self):
        """Test marking a feed sync as successful"""
        feed = FeedRegistry.objects.create(
            name="Test Feed",
            source_url="https://example.com/feed.csv",
            feed_type="csv",
            company=self.company
        )
        
        original_next_sync = feed.next_sync
        feed.mark_sync_success(100)
        
        # Refresh from database
        feed.refresh_from_db()
        
        # Check that stats were updated
        self.assertEqual(feed.sync_status, FeedRegistry.SyncStatus.SUCCESS)
        self.assertEqual(feed.last_import_count, 100)
        self.assertEqual(feed.total_imports, 1)
        self.assertEqual(feed.total_iocs, 100)
        self.assertIsNotNone(feed.last_sync)
        
        # Next sync should be updated
        self.assertNotEqual(feed.next_sync, original_next_sync)
    
    def test_mark_sync_failure(self):
        """Test marking a feed sync as failed"""
        feed = FeedRegistry.objects.create(
            name="Test Feed",
            source_url="https://example.com/feed.csv",
            feed_type="csv",
            company=self.company
        )
        
        feed.mark_sync_failure("Connection error")
        
        # Refresh from database
        feed.refresh_from_db()
        
        # Check that stats were updated
        self.assertEqual(feed.sync_status, FeedRegistry.SyncStatus.FAILURE)
        self.assertEqual(feed.error_count, 1)
        self.assertEqual(feed.last_error, "Connection error")
        self.assertIsNotNone(feed.last_sync)
        
        # Next sync should be soon (1 hour) due to failure
        hour_from_now = timezone.now() + timedelta(hours=1)
        self.assertTrue(
            feed.next_sync <= hour_from_now,
            "next_sync should be set to retry soon after failure"
        )
    
    def test_disabled_feed(self):
        """Test that disabled feeds behave correctly"""
        feed = FeedRegistry.objects.create(
            name="Disabled Feed",
            source_url="https://example.com/feed.csv",
            feed_type="csv",
            company=self.company,
            enabled=False
        )
        
        # Refresh from database
        feed.refresh_from_db()
        
        # Check that disabled feed has correct status and no next_sync
        self.assertEqual(feed.sync_status, FeedRegistry.SyncStatus.DISABLED)
        self.assertIsNone(feed.next_sync)
        
        # Test enabling the feed
        feed.enabled = True
        feed.save()
        
        # Refresh from database
        feed.refresh_from_db()
        
        # Check that next_sync is now set
        self.assertIsNotNone(feed.next_sync) 