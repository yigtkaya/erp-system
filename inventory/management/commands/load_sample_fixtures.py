from django.core.management.base import BaseCommand
from inventory.models import Fixture, Status

class Command(BaseCommand):
    help = 'Load sample fixture data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        Fixture.objects.all().delete()

        # Sample fixture data
        fixtures = [
            {
                'code': 'F001',
                'name': 'Universal Vise',
                'status': Status.AVAILABLE
            },
            {
                'code': 'F002',
                'name': 'Angle Plate',
                'status': Status.AVAILABLE
            },
            {
                'code': 'F003',
                'name': 'Rotary Table',
                'status': Status.AVAILABLE
            },
            {
                'code': 'F004',
                'name': 'V-Block Set',
                'status': Status.AVAILABLE
            },
            {
                'code': 'F005',
                'name': 'Indexing Head',
                'status': Status.AVAILABLE
            }
        ]

        for fixture_data in fixtures:
            Fixture.objects.create(**fixture_data)

        self.stdout.write(self.style.SUCCESS('Successfully loaded sample fixture data')) 