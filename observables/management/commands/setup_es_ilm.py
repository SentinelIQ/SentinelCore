import logging
from elasticsearch import Elasticsearch, NotFoundError
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger('api.observables')

class Command(BaseCommand):
    help = 'Sets up Index Lifecycle Management (ILM) policy for observables in Elasticsearch'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Elasticsearch ILM policy for observables...')
        
        # Connect to Elasticsearch
        es_client = Elasticsearch(
            hosts=settings.ELASTICSEARCH_HOSTS,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
            verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
        )
        
        # Check if ES is available
        if not es_client.ping():
            self.stderr.write(self.style.ERROR('Unable to connect to Elasticsearch'))
            return
        
        # Define the lifecycle policy
        policy_name = "observable_retention_policy"
        policy_body = {
            "policy": {
                "phases": {
                    "hot": {
                        "min_age": "0ms",
                        "actions": {
                            "rollover": {
                                "max_age": "30d",
                                "max_size": "50gb"
                            },
                            "set_priority": {
                                "priority": 100
                            }
                        }
                    },
                    "warm": {
                        "min_age": "30d",
                        "actions": {
                            "shrink": {
                                "number_of_shards": 1
                            },
                            "forcemerge": {
                                "max_num_segments": 1
                            },
                            "set_priority": {
                                "priority": 50
                            }
                        }
                    },
                    "delete": {
                        "min_age": "90d",
                        "actions": {
                            "delete": {}
                        }
                    }
                }
            }
        }
        
        # Try to create or update the policy
        try:
            # Check if policy exists
            try:
                existing_policy = es_client.ilm.get_lifecycle(name=policy_name)
                self.stdout.write(f'Updating existing ILM policy: {policy_name}')
            except NotFoundError:
                self.stdout.write(f'Creating new ILM policy: {policy_name}')
            
            # Create or update the policy
            es_client.ilm.put_lifecycle(name=policy_name, policy=policy_body)
            self.stdout.write(self.style.SUCCESS(f'Successfully set up ILM policy: {policy_name}'))
            
            # Create index template for observables to automatically use the policy
            template_name = "observables_template"
            template_body = {
                "index_patterns": ["observables_*"],
                "template": {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "index.lifecycle.name": policy_name,
                        "index.lifecycle.rollover_alias": "observables"
                    }
                }
            }
            
            # Create or update the template
            es_client.indices.put_index_template(name=template_name, body=template_body)
            self.stdout.write(self.style.SUCCESS(f'Successfully set up index template: {template_name}'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error setting up Elasticsearch ILM policy: {str(e)}'))
            logger.error(f'Error setting up Elasticsearch ILM policy: {str(e)}', exc_info=True)
            return
        
        self.stdout.write(self.style.SUCCESS(
            'Elasticsearch ILM setup complete. Observables will be retained for 90 days by default.'
        )) 