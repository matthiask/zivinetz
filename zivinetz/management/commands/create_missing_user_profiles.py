from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from zivinetz.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile objects for users who do not have one'

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0
        
        for user in User.objects.all():
            # Skip if user already has a profile
            if UserProfile.objects.filter(user=user).exists():
                skipped_count += 1
                continue

            # Determine user type based on permissions
            if user.is_staff and not user.is_superuser:
                user_type = "squad_leader"
            elif user.is_superuser:
                user_type = "admin"
            else:
                user_type = "drudge"

            # Create the UserProfile
            UserProfile.objects.create(user=user, user_type=user_type)
            created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created UserProfile for {user.username} with type: {user_type}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} UserProfile objects. '
                f'Skipped {skipped_count} users who already had profiles.'
            )
        ) 