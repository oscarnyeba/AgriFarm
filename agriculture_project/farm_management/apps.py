from django.apps import AppConfig


class FarmManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'farm_management'

    def ready(self):
        import farm_management.templatetags.custom_filters
