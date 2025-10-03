from django.core.management.commands.runserver import Command as RunserverCommand

class Command(RunserverCommand):
    def get_handler(self, *args, **options):
        from django.core.asgi import get_asgi_application
        return get_asgi_application()
