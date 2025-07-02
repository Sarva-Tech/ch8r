from django.apps import AppConfig

from core.qdrant import init_qdrant


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        init_qdrant()
