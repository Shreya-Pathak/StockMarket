from django.db.models import F
import market.models as models
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from django.utils import timezone

#### Need to check if both orders from same folio, stock, price get cancelled
def trigger():
	print('Order Matching')
	with models.LockedAtomicTransaction([models.BuySellOrder]):

		###Iterate over all buy orders
		for order in models.BuySellOrder.objects.filter(order_type = 'Buy'):

			print(order.order_type)
			print(order.order_id)
			rem_quantity = order.quantity - order.completed_quantity
			if rem_quantity == 0:
				continue

			order_match_set = models.BuySellOrder.objects.filter(
					sid_id = order.sid_id
			).filter(
					eid_id = order.eid_id
			).filter(
					order_type = 'Sell'
			).filter(
					price  = order.price
			).filter(
					quantity__gt = F('completed_quantity')
			)

			previous_price = models.StockPriceHistory.timescale.filter(sid = order.sid, eid = order.eid).last().price
			total_stocks   = models.Stock.objects.get(sid = order.sid.sid).total_stocks
			print(previous_price, total_stocks)
			# print(models.)
			###Exchange happens
			if len(order_match_set) > 0:
				new_stock_entry = models.StockPriceHistory(sid = order.sid,
															eid = order.eid,
															creation_time = timezone.now(),
															price = order.price
															)
				new_stock_entry.save()

				###Find Relevant Indices
				index_match = models.PartOfIndex.objects.filter(iid__eid = order.eid, sid = order.sid).values('iid')
				###Index weightage: Presently One-to-One Market-Cap
				for index_id in index_match:
					previous_index = models.IndexPriceHistory.timescale.filter(iid = models.Indices.objects.get(iid = index_id['iid'])).last().price
					new_index = previous_index + (order.price - previous_price)*total_stocks
					print(new_index)
					new_index_entry = models.IndexPriceHistory(iid = models.Indices.objects.get(iid = index_id['iid']),
																creation_time = timezone.now(),
																price = new_index)
					new_index_entry.save() 

					# new_entry = models.IndexPriceHistory()


			###Get hold of holdings
			buy_stock_holding = models.Holdings.objects.filter(folio_id = order.folio_id, sid = order.sid).first()
			if buy_stock_holding is None:
				buy_stock_holding = models.Holdings(folio_id = order.folio_id, sid = order.sid, quantity = 0, price = 0)

			###Match Orders
			for order_match in order_match_set:
				print(f'Matching:{order_match.order_id}')

				sell_stock_holding = models.Holdings.objects.filter(folio_id = order_match.folio_id, sid = order_match.sid).first()
				if sell_stock_holding is None:
					sell_stock_holding = models.Holdings(folio_id = order_match.folio_id, sid = order_match.sid, quantity = 0, price = 0)

				rem_quantity_match = order_match.quantity - order_match.completed_quantity				
				print(rem_quantity_match)
				
				if rem_quantity < rem_quantity_match:
					### sell rem_quantity
					sell_stock_holding.quantity = sell_stock_holding.quantity - rem_quantity
					sell_stock_holding.total_price    = sell_stock_holding.total_price - rem_quantity * order.price
					buy_stock_holding.quantity  = buy_stock_holding.quantity  + rem_quantity
					buy_stock_holding.total_price     = buy_stock_holding.total_price  + rem_quantity * order.price

					order_match.completed_quantity = order_match.completed_quantity + rem_quantity
					rem_quantity = 0
				
				else:
					### sell rem_quantity_match
					sell_stock_holding.quantity = sell_stock_holding.quantity - rem_quantity_match
					sell_stock_holding.total_price    = sell_stock_holding.total_price - rem_quantity_match * order.price
					buy_stock_holding.quantity  = buy_stock_holding.quantity + rem_quantity_match
					buy_stock_holding.total_price     = buy_stock_holding.total_price + rem_quantity_match * order.price
					rem_quantity -= rem_quantity_match
					order_match.completed_quantity += order.quantity

				if sell_stock_holding.quantity == 0:
					sell_stock_holding.delete()
				else:
					sell_stock_holding.save(update_fields = ['quantity', 'total_price'])
				order_match.save(update_fields = ['completed_quantity'])

			buy_stock_holding.save(update_fields = ['quantity', 'total_price'])
			order.completed_quantity = order.quantity - rem_quantity
			order.save(update_fields = ['completed_quantity'])

		###Delete completed orders
		completed_set = models.BuySellOrder.objects.filter(quantity = F('completed_quantity'))
		for completed_order in completed_set:
			oldorder = models.OldOrder(folio_id=completed_order.folio_id, 
                                            bid=completed_order.bid, 
                                            eid=completed_order.eid,
                                            sid=completed_order.sid, 
                                            quantity=completed_order.quantity, 
                                            price=completed_order.price, 
                                            creation_time=completed_order.creation_time, 
                                            order_type=completed_order.order_type)
			oldorder.save()
			completed_order.delete()

def start_scheduler(interval=5):
    scheduler = BackgroundScheduler()
    scheduler.add_job(trigger, 'interval', seconds=interval)
    scheduler.start()