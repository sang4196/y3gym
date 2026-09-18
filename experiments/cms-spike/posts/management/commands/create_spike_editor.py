import getpass
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from posts.test_support import configure_editor


class Command(BaseCommand):
    help = "Interactively create a local ordinary SPIKE-01 editor; never prints passwords."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, username, **options):
        if get_user_model().objects.filter(username=username).exists():
            raise CommandError("Account exists. It was not changed.")
        password = getpass.getpass("Local test password: ")
        if len(password) < 12 or password != getpass.getpass("Repeat local test password: "):
            raise CommandError("Passwords must match and contain at least 12 characters.")
        user = get_user_model().objects.create_user(username=username, password=password, is_staff=True)
        configure_editor(user)
        self.stdout.write("Local ordinary editor created. No superuser or deletion permission.")
