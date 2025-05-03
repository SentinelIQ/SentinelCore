from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Generate migrations for the Observable model updates'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating migrations for observables app...'))
        
        # Create migrations for the observables app
        call_command('makemigrations', 'observables')
        
        self.stdout.write(self.style.SUCCESS('Migrations created successfully!'))
        self.stdout.write(self.style.WARNING(
            'Next steps:\n'
            '1. Review the generated migrations\n'
            '2. Apply migrations with: docker compose exec web python manage.py migrate\n'
            '3. After migrating, update any code that references observable types to use the new format'
        )) 