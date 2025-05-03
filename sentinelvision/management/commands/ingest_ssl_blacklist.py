import json
from django.core.management.base import BaseCommand
from django.utils.termcolors import colorize
from companies.models import Company
from sentinelvision.feeds.ssl_blacklist_feed import SSLBlacklistFeed

class Command(BaseCommand):
    help = 'Ingest SSL Blacklist data into Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Optional company ID to ingest data for'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )

    def handle(self, *args, **options):
        company_id = options.get('company')
        
        self.stdout.write(self.style.SUCCESS("Starting SSL Blacklist ingestion to Elasticsearch"))
        
        if company_id:
            # Run for specific company
            try:
                company = Company.objects.get(id=company_id)
                self.stdout.write(f"Running for company: {company.name} (ID: {company.id})")
                
                feed_instance, created = SSLBlacklistFeed.objects.get_or_create(
                    company=company,
                    defaults={
                        'name': 'SSL Certificate Blacklist',
                        'feed_url': 'https://sslbl.abuse.ch/blacklist/sslblacklist.csv'
                    }
                )
                
                result = feed_instance.update_feed()
                self._display_result(result, options['json'])
                
            except Company.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Company with ID {company_id} not found"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
        else:
            # Run for all companies
            self.stdout.write("Running for all companies")
            
            companies = Company.objects.all()
            if not companies.exists():
                self.stderr.write(self.style.WARNING("No companies found"))
                return
            
            results = []
            
            for company in companies:
                self.stdout.write(f"Processing company: {company.name}")
                
                try:
                    feed_instance, created = SSLBlacklistFeed.objects.get_or_create(
                        company=company,
                        defaults={
                            'name': 'SSL Certificate Blacklist',
                            'feed_url': 'https://sslbl.abuse.ch/blacklist/sslblacklist.csv'
                        }
                    )
                    
                    result = feed_instance.update_feed()
                    results.append({
                        'company': company.name,
                        'company_id': str(company.id),
                        **result
                    })
                    
                    # Display individual result unless in JSON mode
                    if not options['json']:
                        status = result.get('status', 'unknown')
                        color = 'green' if status == 'success' else 'red'
                        processed = result.get('processed_count', 0)
                        
                        self.stdout.write(f"  - {company.name}: {colorize(status, fg=color)} ({processed} records)")
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"  - Error for {company.name}: {str(e)}"))
                    results.append({
                        'company': company.name,
                        'company_id': str(company.id),
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Display overall results in JSON mode
            if options['json']:
                self.stdout.write(json.dumps({
                    'status': 'complete',
                    'companies_processed': len(results),
                    'results': results
                }, indent=2))
            else:
                self.stdout.write(self.style.SUCCESS(f"Processed {len(results)} companies"))
    
    def _display_result(self, result, json_format):
        """Display the result of a feed update"""
        if json_format:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            status = result.get('status', 'unknown')
            color = 'green' if status == 'success' else 'red'
            
            self.stdout.write(self.style.SUCCESS(f"Status: {colorize(status, fg=color)}"))
            
            if status == 'success':
                processed = result.get('processed_count', 0)
                self.stdout.write(f"Records processed: {processed}")
                self.stdout.write(f"Message: {result.get('message', '')}")
            else:
                self.stdout.write(self.style.ERROR(f"Error: {result.get('error', 'Unknown error')}")) 