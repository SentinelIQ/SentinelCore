import json
from django.core.management.base import BaseCommand
from django.utils.termcolors import colorize

class Command(BaseCommand):
    help = 'Run the centralized feed dispatcher to update all feeds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Optional company ID to run feeds for'
        )
        parser.add_argument(
            '--feed-types',
            nargs='+',
            help='Optional list of specific feed types to update'
        )
        parser.add_argument(
            '--concurrent',
            action='store_true',
            help='Run feeds concurrently (default: sequential)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=3600,
            help='Timeout for task execution in seconds (default: 3600)'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )

    def handle(self, *args, **options):
        from sentinelvision.tasks.feed_dispatcher import update_all_feeds
        
        company_id = options.get('company')
        feed_types = options.get('feed_types')
        concurrent = options.get('concurrent', False)
        timeout = options.get('timeout', 3600)
        
        self.stdout.write(self.style.SUCCESS("Running centralized feed dispatcher"))
        self.stdout.write(f"  Concurrent mode: {concurrent}")
        if company_id:
            self.stdout.write(f"  Company ID: {company_id}")
        if feed_types:
            self.stdout.write(f"  Feed types: {', '.join(feed_types)}")
        self.stdout.write(f"  Timeout: {timeout} seconds")
        
        # Run the dispatcher
        try:
            result = update_all_feeds(
                company_id=company_id, 
                feed_types=feed_types,
                concurrent=concurrent,
                timeout=timeout
            )
            
            # Display the result
            if options['json']:
                self.stdout.write(json.dumps(result, indent=2))
            else:
                status = result.get('status', 'unknown')
                color = 'green' if status in ('success', 'complete') else 'yellow' if status == 'scheduled' else 'red'
                
                self.stdout.write(self.style.SUCCESS(f"Feed dispatcher completed with status: {colorize(status, fg=color)}"))
                
                if status == 'scheduled':
                    self.stdout.write(f"Scheduled {result.get('feeds_scheduled', 0)} feed tasks (concurrent mode)")
                    self.stdout.write("Use Celery Flower or task IDs to check results:")
                    for feed_id, task_id in result.get('task_ids', {}).items():
                        self.stdout.write(f"  - {feed_id}: {task_id}")
                    
                elif status == 'complete':
                    self.stdout.write(f"Processed {result.get('feeds_processed', 0)} feed tasks (sequential mode)")
                    self.stdout.write(f"  Successful: {result.get('successful', 0)}")
                    self.stdout.write(f"  Failed: {result.get('failed', 0)}")
                    
                    # Show results for each feed
                    for feed_result in result.get('results', []):
                        feed_id = feed_result.get('feed_id')
                        feed_status = feed_result.get('status')
                        result_color = 'green' if feed_status == 'success' else 'red'
                        self.stdout.write(f"  - {feed_id}: {colorize(feed_status, fg=result_color)}")
                        
                        if feed_status == 'error':
                            self.stdout.write(f"    Error: {feed_result.get('error', 'Unknown error')}")
                
                elif status == 'error':
                    self.stdout.write(self.style.ERROR(f"Error: {result.get('error')}"))
                    
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error executing feed dispatcher: {str(e)}")) 