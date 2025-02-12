from django.core.management.base import BaseCommand
from erp_core.models import User, UserProfile

class Command(BaseCommand):
    help = 'Creates UserProfile for users that do not have one'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        created_count = 0

        for user in users_without_profile:
            # Skip creating profile for AnonymousUser
            if user.username == 'AnonymousUser':
                continue
                
            UserProfile.objects.create(
                user=user,
                employee_id=f'EMP{user.id:04d}'  # Generate a default employee ID
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} user profiles'
            )
        ) 