from django.apps import AppConfig
import os


class MarketConfig(AppConfig):
    name = 'market'

    # def ready(self):
    #     from . import jobs
    #     if os.environ.get('RUN_MAIN', None) != 'true':
    #         jobs.start_scheduler()
