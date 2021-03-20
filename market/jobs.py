from django.db.models import F
import market.models as models
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from django.utils import timezone

#### Need to check if both orders from same folio, stock, price get cancelled
def trigger():
    print('Order Matching')
    stockpricehistory_list = []
    indexpricehistory_list = []
    oldorder_list = []

    with models.LockedAtomicTransaction([models.BuySellOrder]):

        ###Iterate over all buy orders
        for order in models.BuySellOrder.objects.select_related('sid').filter(order_type='Buy'):
            print('Current Order :', order.order_id, '| type =', order.order_type)

            order_match_set = models.BuySellOrder.objects.filter(
                sid=order.sid,
                eid=order.eid,
                order_type='Sell',
                price=order.price,
                quantity__gt=F('completed_quantity')
            )

            try:
                Stocklists_entry = models.Stocklists.objects.get(sid=order.sid, eid=order.eid)
            except Exception as e:
                print(order.sid.ticker)
                print(order.eid.name)
            previous_price = Stocklists_entry.last_price
            total_stocks = order.sid.total_stocks
            print('Stock =', order.sid.ticker, '| Previous price =', previous_price, '| Total Stocks =', total_stocks)

            # Exchange happens, so update index prices and stock prices
            if len(order_match_set) > 0:
                new_stock_entry = models.StockPriceHistory(
                    sid=order.sid,
                    eid=order.eid,
                    creation_time=timezone.now(),
                    price=order.price
                )
                stockpricehistory_list.append(new_stock_entry)

                # Find Relevant Indices
                index_match = models.PartOfIndex.objects.select_related('iid').filter(iid__eid=order.eid, sid=order.sid)
                
                # Index weightage: Presently One-to-One Market-Cap
                for index_id in index_match:

                    index_object = index_id.iid
                    index_object.last_price += (order.price - previous_price) * total_stocks / index_object.base_divisor
                    new_index_entry = models.IndexPriceHistory(
                        iid=index_object,
                        creation_time=timezone.now(),
                        price=index_object.last_price
                    )
                    index_object.save(update_fields=['last_price'])
                    indexpricehistory_list.append(new_index_entry)

                Stocklists_entry.last_price = order.price
                Stocklists_entry.save(update_fields=['last_price'])

            # Get hold of holdings
            buy_stock_holding = models.Holdings.objects.filter(folio_id=order.folio_id, sid=order.sid).first()
            if buy_stock_holding is None:
                buy_stock_holding = models.Holdings(folio_id=order.folio_id, sid=order.sid, quantity=0, price=0)

            rem_quantity = order.quantity - order.completed_quantity
            assert rem_quantity != 0
            ###Match Orders
            for order_match in order_match_set:
                if rem_quantity == 0: break
                print(f'Matching:{order_match.order_id}')

                sell_stock_holding = models.Holdings.objects.filter(folio_id=order_match.folio_id, sid=order_match.sid).first()
                if sell_stock_holding is None:
                    ###Error report
                    # print("fault")
                    continue
                    sell_stock_holding = models.Holdings(folio_id=order_match.folio_id, sid=order_match.sid, quantity=0, total_price=0)

                
                quantity_match = min(rem_quantity, order_match.quantity - order_match.completed_quantity)
                rem_quantity -= quantity_match
                order_match.completed_quantity += quantity_match
                order_match.save(update_fields=['completed_quantity'])


                sell_stock_holding.quantity -= quantity_match
                sell_stock_holding.total_price -= quantity_match * order.price
                buy_stock_holding.quantity += quantity_match
                buy_stock_holding.total_price += quantity_match * order.price

                if sell_stock_holding.quantity == 0:
                    sell_stock_holding.delete()
                else:
                    sell_stock_holding.save(update_fields=['quantity', 'total_price'])

            buy_stock_holding.save(update_fields=['quantity', 'total_price'])
            order.completed_quantity = order.quantity - rem_quantity
            order.save(update_fields=['completed_quantity'])

        # Delete completed orders
        completed_orders = models.BuySellOrder.objects.filter(quantity=F('completed_quantity'))
        for completed_order in completed_orders:
            oldorder = models.OldOrder(
                folio_id=completed_order.folio_id, 
                bid=completed_order.bid, 
                eid=completed_order.eid,
                sid=completed_order.sid, 
                quantity=completed_order.quantity, 
                price=completed_order.price, 
                creation_time=completed_order.creation_time, 
                order_type=completed_order.order_type
            )
            oldorder_list.append(oldorder)
        completed_orders.delete()

    models.OldOrder.objects.bulk_create(oldorder_list)
    models.StockPriceHistory.objects.bulk_create(stockpricehistory_list)
    models.IndexPriceHistory.objects.bulk_create(indexpricehistory_list)


def start_scheduler(interval=5):
    scheduler = BackgroundScheduler()
    scheduler.add_job(trigger, 'interval', seconds=interval)
    scheduler.start()