from django.apps import AppConfig
from sc_client import client


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    def ready(self):
        client.connect("ws://localhost:8090/ws_json")

