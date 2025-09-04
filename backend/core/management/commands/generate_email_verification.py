# core/management/commands/generate_email_verification.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User  # default User model
from core.services.encryption import generate_verification_token

class Command(BaseCommand):
    help = 'Generate email verification link for an existing user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to generate verification link for',
            required=True
        )

    def handle(self, *args, **options):
        email = options['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} does not exist'))
            return

        token = generate_verification_token(user.id, user.email)

        base_url = settings.API_BASE_URL.rstrip('/')  # backend API URL
        verification_link = f"{base_url}/verify-email/{token}/"

        self.stdout.write(self.style.SUCCESS(f'Verification link for {email}:'))
        self.stdout.write(verification_link)
