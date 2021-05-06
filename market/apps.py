from django.apps import AppConfig
import os


class MarketConfig(AppConfig):
    name = 'market'

    def ready(self):
        from . import jobs
        mv = jobs.custom_query("""
	        CREATE materialized view if not exists closing_price_ind as 
	        select time_bucket('1 day', creation_time) date, last(price, creation_time) price, 
	        iid from market_indexpricehistory group by date, iid order by iid, date with no data;""")
        dr1 = jobs.custom_query("""
	        CREATE materialized view if not exists daily_return_ind as 
	        SELECT date, ((price/lag(price, 1) over (partition by (iid) order by date))-1) dr, iid from closing_price_ind with no data;""")
        mv = jobs.custom_query("""
	        CREATE materialized view if not exists closing_price as 
	        select time_bucket('1 day', creation_time) date, last(price, creation_time) price, 
	        sid, eid from market_stockpricehistory group by date, sid, eid order by sid, eid,date with no data;""")
        dr1 = jobs.custom_query("""
	        CREATE materialized view if not exists daily_return as 
	        SELECT date, ((price/lag(price, 1) over (partition by (sid, eid) order by date))-1) dr, sid, eid from closing_price with no data;""")
        if os.environ.get('RUN_MAIN', None) != 'true':
            jobs.start_scheduler()
