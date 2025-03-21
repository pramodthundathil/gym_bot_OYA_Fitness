from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Members'

    def ready(self):
        from . import signals
        from .management.commands import update_member_status
        
