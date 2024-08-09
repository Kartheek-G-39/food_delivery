from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
from django.apps import AppConfig

class CoreAppConfig(AppConfig):
    name = 'core'

    def ready(self):
        from . import tasks  # Import signals to ensure they are registered
        from .tasks import start_check_undelivered_orders_thread
        start_check_undelivered_orders_thread()
