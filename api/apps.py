from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    App configuration for the API module.

    Django loads this class when the app starts. 
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
