import psycopg2

name = "proj"
user = "postgres"
pswd = "postgres"
host = "127.0.0.1"
port = "5432"
conn=psycopg2.connect(host=host,database=name,user=user,password=pswd,port=port)
cursor=conn.cursor()




q1 = """
	        CREATE materialized view if not exists closing_price_ind as 
	        select time_bucket('1 day', creation_time) date, last(price, creation_time) price, 
	        iid from market_indexpricehistory group by date, iid order by iid, date with no data;"""
q2 = """
    CREATE materialized view if not exists daily_return_ind as 
    SELECT date, ((price/lag(price, 1) over (partition by (iid) order by date))-1) dr, iid from closing_price_ind with no data;"""
q3 = """
    CREATE materialized view if not exists closing_price as 
    select time_bucket('1 day', creation_time) date, last(price, creation_time) price, 
    sid, eid from market_stockpricehistory group by date, sid, eid order by sid, eid,date with no data;"""
q4 = """
    CREATE materialized view if not exists daily_return as 
    SELECT date, ((price/lag(price, 1) over (partition by (sid, eid) order by date))-1) dr, sid, eid from closing_price with no data;"""
q5="REFRESH MATERIALIZED VIEW closing_price_ind ;"
q6="REFRESH MATERIALIZED VIEW daily_return_ind ;"
q7="REFRESH MATERIALIZED VIEW closing_price ;"
q8="REFRESH MATERIALIZED VIEW daily_return ;"

for q in [q1,q2,q3,q4,q5,q6,q7,q8]:
	print(q)
	cursor.execute(q)
conn.commit()
cursor.close()