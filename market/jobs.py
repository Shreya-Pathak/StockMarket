from django.db.models import F
import market.models as models
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


def trigger():
    # with models.LockedAtomicTransaction([models.BuySellOrder]):
	    # add trigger logic
	    # print('Time is {}'.format(datetime.now().time()))
    pass


def start_scheduler(interval=5):
    scheduler = BackgroundScheduler()
    scheduler.add_job(trigger, 'interval', seconds=interval)
    scheduler.start()
