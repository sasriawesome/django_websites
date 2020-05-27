from django.apps import AppConfig as AppConfigBase


class AppConfig(AppConfigBase):
    name = 'django_websites'
    label = 'django_websites'
    verbose_name = 'Django Website'
