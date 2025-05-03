import json
from django.core.management.base import BaseCommand
from django.utils.termcolors import colorize

class Command(BaseCommand):
    help = 'Run a specific feed task for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            'feed_id',
            type=str,
            help='ID of the feed to run (e.g., ssl_blacklist)'
        )
        parser.add_argument(
            '--company',
            type=str,
            help='Optional company ID to run the feed for'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )

    def handle(self, *args, **options):
        from sentinelvision.feeds import get_feed_task
        
        feed_id = options['feed_id']
        company_id = options.get('company')
        
        self.stdout.write(f"Running feed task for: {feed_id}")
        
        # Get the task
        feed_task = get_feed_task(feed_id)
        
        if not feed_task:
            self.stderr.write(self.style.ERROR(f"Feed task not found for: {feed_id}"))
            return
        
        # Run the task synchronously
        self.stdout.write(f"Executing task: {feed_task.name}")
        
        try:
            if company_id:
                self.stdout.write(f"Running for company: {company_id}")
                result = feed_task(company_id=company_id)
            else:
                self.stdout.write("Running for all companies")
                result = feed_task()
            
            # Display the result
            if options['json']:
                self.stdout.write(json.dumps(result, indent=2))
            else:
                status = result.get('status', 'unknown')
                color = 'green' if status == 'success' else 'red' if status == 'error' else 'yellow'
                
                self.stdout.write(self.style.SUCCESS(f"Task completed with status: {colorize(status, fg=color)}"))
                
                if status == 'success':
                    companies_processed = result.get('companies_processed', 0)
                    self.stdout.write(f"Companies processed: {companies_processed}")
                    
                    for company_result in result.get('results', []):
                        company_name = company_result.get('company')
                        company_status = company_result.get('status')
                        processed = company_result.get('processed_count', 0)
                        
                        result_color = 'green' if company_status == 'success' else 'red'
                        self.stdout.write(f"  - {company_name}: {colorize(company_status, fg=result_color)} ({processed} IOCs)")
                
                elif status == 'error':
                    self.stdout.write(self.style.ERROR(f"Error: {result.get('error')}"))
                    
                    if result.get('is_retrying'):
                        self.stdout.write("Task will be retried automatically")
        
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error executing task: {str(e)}")) 