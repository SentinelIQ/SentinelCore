import json
from django.core.management.base import BaseCommand
from django.utils.termcolors import colorize

class Command(BaseCommand):
    help = 'List all available feed tasks in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        parser.add_argument(
            '--with-dispatcher',
            action='store_true',
            help='Show information about the centralized dispatcher'
        )

    def handle(self, *args, **options):
        from sentinelvision.feeds import get_all_feeds, get_all_feed_tasks
        
        # Get all registered feeds and their tasks
        feeds = get_all_feeds()
        feed_tasks = get_all_feed_tasks()
        
        if options['json']:
            # JSON output format
            feed_data = []
            for feed_id, feed_class in feeds.items():
                feed_info = {
                    'feed_id': feed_id,
                    'name': feed_class._meta.verbose_name,
                    'description': feed_class.__doc__.strip() if feed_class.__doc__ else '',
                    'task_name': f"sentinelvision.feeds.{feed_id}.update",
                    'is_registered': feed_id in feed_tasks
                }
                feed_data.append(feed_info)
            
            result = {
                'count': len(feed_tasks),
                'feeds': feed_data
            }
            
            # Add dispatcher information if requested
            if options['with_dispatcher']:
                result['dispatcher'] = {
                    'task_name': 'sentinelvision.tasks.feed_dispatcher.update_all_feeds',
                    'description': 'Centralized dispatcher that discovers and updates all registered feed modules',
                    'beat_schedule': 'Every 15 minutes (concurrent execution)',
                    'dynamically_discovered_feeds': len(feeds)
                }
                
            self.stdout.write(json.dumps(result, indent=2))
        else:
            # Pretty formatted output
            self.stdout.write(self.style.SUCCESS(f"Found {len(feeds)} feed modules:"))
            self.stdout.write("")
            
            for feed_id, feed_class in feeds.items():
                status = "✓" if feed_id in feed_tasks else "✗"
                color = "green" if feed_id in feed_tasks else "red"
                
                self.stdout.write(
                    f"{colorize(status, fg=color)} {feed_id}: "
                    f"{feed_class._meta.verbose_name}"
                )
                
                # Show task name
                task_name = f"sentinelvision.feeds.{feed_id}.update"
                self.stdout.write(f"  Task: {task_name}")
                
                # Show description if available
                if feed_class.__doc__:
                    self.stdout.write(f"  {feed_class.__doc__.strip()}")
                
                self.stdout.write("")
            
            # Show dispatcher information if requested
            if options['with_dispatcher']:
                self.stdout.write(self.style.SUCCESS("Centralized Feed Dispatcher:"))
                self.stdout.write(colorize("✓", fg="green") + " Task: sentinelvision.tasks.feed_dispatcher.update_all_feeds")
                self.stdout.write("  Scheduled: Every 15 minutes (concurrent execution)")
                self.stdout.write(f"  Managing: {len(feeds)} dynamically discovered feed modules")
                self.stdout.write("  Parameters:")
                self.stdout.write("    - company_id: Optional UUID of specific company to update for")
                self.stdout.write("    - feed_types: Optional list of specific feed types to update")
                self.stdout.write("    - concurrent: Whether to execute feeds concurrently (default: True)")
                self.stdout.write("    - timeout: Timeout for task execution in seconds (default: 3600)")
                self.stdout.write("") 