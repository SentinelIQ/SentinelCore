from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from sentinelvision.models import FeedRegistry
from sentinelvision.tasks.feed_tasks import update_feed, schedule_pending_feeds, retry_failed_feeds
from sentinelvision.feeds import get_feed_class
from sentinelvision.logging import get_structured_logger

logger = get_structured_logger('sentinelvision.tests')


class FakeCeleryTask:
    """Mock for Celery task with delay and apply_async methods"""
    
    def __init__(self, return_value=None, raises=None):
        self.return_value = return_value
        self.raises = raises
        self.called_with_args = None
        self.called_with_kwargs = None
    
    def delay(self, *args, **kwargs):
        self.called_with_args = args
        self.called_with_kwargs = kwargs
        if self.raises:
            raise self.raises
        return self.return_value
    
    def apply_async(self, *args, **kwargs):
        self.called_with_args = args
        self.called_with_kwargs = kwargs
        return self
    
    def get(self):
        if self.raises:
            raise self.raises
        return self.return_value
    
    def s(self, *args, **kwargs):
        self.called_with_args = args
        self.called_with_kwargs = kwargs
        return self


class MockFeed:
    """Mock for generic feed class"""
    
    def update_feed(self, *args, **kwargs):
        # Return mock success result
        return {
            'status': 'success',
            'processed_count': 50,
            'timestamp': timezone.now().isoformat()
        }


class TestFeedTasks(TestCase):
    """Test suite for feed tasks"""
    
    def setUp(self):
        self.feed_registry = FeedRegistry.objects.create(
            name="Test Feed",
            feed_type="test_feed",
            source_url="http://test.com/feed",
            enabled=True
        )
    
    @patch('sentinelvision.feeds.get_feed_class')
    def test_update_feed_success(self, mock_get_feed_class):
        # Mock feed class and instance
        mock_feed_class = MagicMock()
        mock_feed_instance = MagicMock()
        mock_feed_instance.update_feed.return_value = {
            'status': 'success',
            'processed_count': 10
        }
        mock_feed_class.objects.get_or_create.return_value = (mock_feed_instance, True)
        mock_get_feed_class.return_value = mock_feed_class
        
        # Execute task
        result = update_feed(self.feed_registry.id)
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['processed_count'], 10)
        mock_feed_instance.update_feed.assert_called_once()
    
    @patch('sentinelvision.feeds.get_feed_class')
    def test_update_feed_failure(self, mock_get_feed_class):
        # Mock feed class and instance
        mock_feed_class = MagicMock()
        mock_feed_instance = MagicMock()
        mock_feed_instance.update_feed.return_value = {
            'status': 'error',
            'error': 'Test error'
        }
        mock_feed_class.objects.get_or_create.return_value = (mock_feed_instance, True)
        mock_get_feed_class.return_value = mock_feed_class
        
        # Execute task
        result = update_feed(self.feed_registry.id)
        
        # Verify results
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Test error')
        mock_feed_instance.update_feed.assert_called_once()
    
    @patch('sentinelvision.tasks.feed_tasks.update_feed.apply_async')
    def test_schedule_pending_feeds(self, mock_apply_async):
        """Test scheduling pending feeds"""
        # Create a feed that's due for update
        due_feed = FeedRegistry.objects.create(
            name="Due Feed",
            source_url="https://example.com/due.csv",
            feed_type="test_feed",
            sync_interval_hours=12,
            next_sync=timezone.now() - timedelta(hours=1)  # Already due
        )
        
        # Create a feed that's not due yet
        future_feed = FeedRegistry.objects.create(
            name="Future Feed",
            source_url="https://example.com/future.csv",
            feed_type="test_feed",
            sync_interval_hours=12,
            next_sync=timezone.now() + timedelta(hours=1)  # Not due yet
        )
        
        # Create a disabled feed
        disabled_feed = FeedRegistry.objects.create(
            name="Disabled Feed",
            source_url="https://example.com/disabled.csv",
            feed_type="test_feed",
            enabled=False
        )
        
        # Run the scheduling task
        result = schedule_pending_feeds()
        
        # Check that only the due feed was scheduled
        self.assertEqual(result['scheduled_count'], 1)
        mock_apply_async.assert_called_once()
        args, kwargs = mock_apply_async.call_args
        self.assertEqual(kwargs['args'], [str(due_feed.id)])
    
    @patch('sentinelvision.tasks.feed_tasks.update_feed.apply_async')
    def test_retry_failed_feeds(self, mock_apply_async):
        """Test retrying failed feeds"""
        # Create a failed feed
        failed_feed = FeedRegistry.objects.create(
            name="Failed Feed",
            source_url="https://example.com/failed.csv",
            feed_type="test_feed",
            sync_status=FeedRegistry.SyncStatus.FAILURE,
            last_sync=timezone.now() - timedelta(hours=2),
            error_count=1
        )
        
        # Create an old failed feed (more than 24 hours ago)
        old_failed_feed = FeedRegistry.objects.create(
            name="Old Failed Feed",
            source_url="https://example.com/old_failed.csv",
            feed_type="test_feed",
            sync_status=FeedRegistry.SyncStatus.FAILURE,
            last_sync=timezone.now() - timedelta(hours=25),
            error_count=1
        )
        
        # Run the retry task
        result = retry_failed_feeds()
        
        # Check that only the recent failed feed was retried
        self.assertEqual(result['retry_count'], 1)
        mock_apply_async.assert_called_once()
        args, kwargs = mock_apply_async.call_args
        self.assertEqual(kwargs['args'], [str(failed_feed.id)]) 