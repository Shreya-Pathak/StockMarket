from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.models import User
import client.forms as forms
import market.models as models
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from market.views import render


# Create your views here.
def check_type(v, t=int):
	try:
		return t(v)
	except:
		return None


def check_user(request):
	if not request.user.is_authenticated:
		return False
	client = models.Client.objects.filter(username=request.user.username).first()
	if client is None:
		messages.warning(request, 'You do not have access to this page.')
		return True
	return False


def index_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if request.user.is_authenticated:
		return HttpResponseRedirect('home')
	else:
		return HttpResponseRedirect('/login')


def logout_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if request.user.is_authenticated:
		logout(request)
		messages.info(request, 'Successfully logged out.')
	return HttpResponseRedirect('/login')


def home_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if not request.user.is_authenticated:
		messages.error(request, 'Please login first.')
		return HttpResponseRedirect('/login')
	client = models.Client.objects.filter(username=request.user.username).first()
	assert client is not None
	context = {'client': client}
	return render(request, 'client/home.html', context)



def portfolio_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if not request.user.is_authenticated:
		messages.error(request, 'Please login first.')
		return HttpResponseRedirect('/login')
	client = models.Client.objects.filter(username=request.user.username).first()
	assert client is not None

	hold_id = check_type(request.GET.get('id', None), int)
	if hold_id is not None:
		holding = models.Holdings.objects.select_related('folio_id').filter(pk=hold_id, folio_id__clid=client).first()
		stock_wish = models.StockWishlist.objects.select_related('wish_id').filter(pk=hold_id, wish_id__clid=client).first()
		if holding is None:
			messages.error(request, 'You can\'t delete this portfolio entry.')
		elif holding.quantity != 0:
			messages.error(request, 'You can\'t delete a non-zero quantity owned portfolio entry.')
		else:
			folio = holding.folio_id
			holding.delete()
			messages.success(request, 'Portfolio entry deleted.')
			if not models.Holdings.objects.filter(folio_id=folio).exists():
				folio.delete()
				messages.success(request, 'Portfolio also deleted.')
		return HttpResponseRedirect('portfolio')

	if request.method == 'POST':
		formdata = forms.PortfolioForm(data=request.POST)
		if formdata.is_valid():
			pname = formdata.cleaned_data['pname']
			stock = formdata.cleaned_data['stock']
			folio = models.Portfolio.objects.filter(pname__iexact=pname, clid=client).first()
			if folio is not None and stock is None:
				messages.error(request,'Portfolio already exists.')
			if folio is None:
				folio = models.Portfolio(pname=pname, clid=client)
				folio.save()
				messages.success(request, 'Portfolio created.')
			if stock is not None:
				holding = models.Holdings.objects.filter(folio_id=folio, sid=stock).first()
				if holding is not None:
					messages.error(request, 'This stock already exists in the specified portfolio.')
					return HttpResponseRedirect('portfolio')
				holding = models.Holdings(folio_id=folio, sid=stock, quantity=0, total_price=0)
				holding.save()
				messages.success(request, 'Stock added to portfolio.')
	data = {}
	for folio in models.Portfolio.objects.filter(clid=client):
		data[folio.pname] = []
	holdings = models.Holdings.objects.select_related('folio_id', 'sid').filter(folio_id__clid=client).order_by('folio_id__pname')
	for holding in holdings:
		data[holding.folio_id.pname].append((holding, holding.sid))
	form = forms.PortfolioForm()
	context = {'data': data, 'form': form}
	return render(request, 'client/portfolio.html', context)


def place_order_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if not request.user.is_authenticated:
		messages.error(request, 'Please login first.')
		return HttpResponseRedirect('/login')

	if request.method == 'POST':
		form = forms.OrderForm(data=request.POST)
		if form.is_valid():
			portfolio = form.cleaned_data['portfolio']
			broker = form.cleaned_data['broker']
			exchange = form.cleaned_data['exchange']
			order_type = form.cleaned_data['order_type']
			stock = form.cleaned_data['stock']
			price = form.cleaned_data['price']
			quantity = form.cleaned_data['quantity']
			client = models.Client.objects.filter(username=request.user.username).first()
			holding = models.Holdings.objects.filter(folio_id=portfolio, sid=stock).first()

			# check all objects are ok
			if any([t is None for t in [client, portfolio, stock, broker, exchange, holding]]) or order_type not in ('Buy', 'Sell'):
				messages.error(request, 'Invalid order.')
				return render(request, 'client/place_order.html', {'form': form})

			
			# add stock to portfolio if doesnt exist
			if holding is None:
				holding = models.Holdings(folio_id=portfolio, sid=stock, quantity=0, total_price=0)
			
			cost = Decimal(quantity * price)
			commission = (broker.commission * cost) / 100

			# check if stock is listed at the exchange
			if not models.ListedAt.objects.filter(sid=stock, eid=exchange).exists():
				messages.error(request, 'Stock is not listed at this exchange.')
			# check if broker is registered at the exchange
			elif not models.RegisteredAt.objects.filter(bid=broker, eid=exchange).exists():
				messages.error(request, 'Broker is not registered at this exchange.')
			# in any order_type, check if commission balance is present
			# if order_type is buy, check if balance is enough
			elif order_type == 'Buy' and client.balance < commission + cost:
				messages.error(request, 'Insufficient balance.')
			# if order_type is sell, check if stock quantity in holdings >= specified holdings
			elif order_type == 'Sell' and (client.balance < commission or holding.quantity < quantity):
				if client.balance < commission:
					messages.error(request, 'Insufficient balance.')
				if holding.quantity < quantity:
					messages.error(request, 'Insufficient stocks.')
			else:
				# create the order
				neworder = models.PendingOrder(folio_id=portfolio, bid=broker, eid=exchange, sid=stock, quantity=quantity, price=price, creation_time=timezone.now(), order_type=order_type)
				# update the holdings and holding balance of client
				if order_type == 'Buy':
					client.balance -= commission + cost
				# total_price in holdings can be negative ideally
				else:
					holding.quantity -= quantity
					holding.total_price -= cost
					client.balance -= commission

				neworder.save()
				client.save()
				broker.save()
				holding.save()

				messages.success(request, 'Your order has been placed.')
				form = forms.OrderForm()
	else:
		form = forms.OrderForm()
	return render(request, 'client/place_order.html', {'form': form})


def cancel_order_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if not request.user.is_authenticated:
		messages.error(request, 'Please login first.')
		return HttpResponseRedirect('/login')
	clid = models.Client.objects.filter(username=request.user.username).first()
	assert clid is not None

	order_id = check_type(request.GET.get('order', None), int)
	order_table = request.GET.get('type', '')
	table_map = {'pending': models.PendingOrder, 'current': models.BuySellOrder}

	if order_id is not None and order_table in table_map.keys():
		order = table_map[order_table].objects.filter(pk=order_id, folio_id__clid=clid).first()
		if order is not None:
			rem_quantity = order.quantity
			if order_table == 'current':
				rem_quantity -= order.completed_quantity
			if order.order_type == 'Buy':
				clid.balance += order.price * rem_quantity
			else:
				if order.order_type == 'current':
					clid.balance += order.price * order.completed_quantity
				holding = models.Holdings.objects.filter(folio_id=order.folio_id, sid=order.sid).first()
				if holding is None:
					messages.error(request, 'Invalid order.')
					return HttpResponseRedirect('cancel_order')
				holding.quantity += rem_quantity
				holding.total_price += rem_quantity * order.price
				holding.save()
			if order_table == 'pending':
				commission = (order.bid.commission * order.quantity * order.price) / 100
				clid.balance += commission
			clid.save()
			order.delete()
			messages.success(request, 'Order cancelled.')
		else:
			messages.error(request, 'This order does not exist.')
		return HttpResponseRedirect('cancel_order')

	pendingorder = models.PendingOrder.objects.select_related('sid', 'eid', 'bid__bid', 'folio_id').filter(folio_id__clid=clid)
	currorder = models.BuySellOrder.objects.select_related('sid', 'eid', 'bid__bid', 'folio_id').filter(folio_id__clid=clid)
	formog = forms.SorterForm()

	if request.method == 'POST':
		form = forms.SorterForm(request.POST)
		if form.is_valid():
			sortfield = form.cleaned_data.get('sortfield')
			order_type = form.cleaned_data.get('order_type')
			ticker = form.cleaned_data.get('ticker')
			exchange = form.cleaned_data.get('exchange')
			broker = form.cleaned_data.get('broker')
			if order_type != 'All':
				pendingorder = pendingorder.filter(order_type=order_type)
				currorder = currorder.filter(order_type=order_type)
				formog.fields['order_type'].initial = order_type
			if sortfield != 'None':
				pendingorder = pendingorder.order_by(sortfield)
				currorder = currorder.order_by(sortfield)
				formog.fields['sortfield'].initial = sortfield
			if ticker != '':
				pendingorder = pendingorder.filter(sid__ticker__icontains=ticker)
				currorder = currorder.filter(sid__ticker__icontains=ticker)
			if exchange != '':
				pendingorder = pendingorder.filter(eid__name__icontains=exchange)
				currorder = currorder.filter(eid__name__icontains=exchange)
			if broker != '':
				pendingorder = pendingorder.filter(bid__bid__name__icontains=broker)
				currorder = currorder.filter(bid__bid__name__icontains=broker)

	context = {'pendingorders': pendingorder.all(), 'currorder': currorder.all(), 'form': formog}
	return render(request, 'client/cancel_order.html', context)


def past_order_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if not request.user.is_authenticated:
		messages.error(request, 'Please login first.')
		return HttpResponseRedirect('/login')
	clid = models.Client.objects.filter(username=request.user.username).first()
	assert clid is not None

	oldorder = models.OldOrder.objects.select_related('sid', 'eid', 'bid__bid', 'folio_id').filter(folio_id__clid=clid)
	formog = forms.SorterForm()

	if request.method == 'POST':
		form = forms.SorterForm(request.POST)
		if form.is_valid():
			sortfield = form.cleaned_data.get('sortfield')
			order_type = form.cleaned_data.get('order_type')
			ticker = form.cleaned_data.get('ticker')
			exchange = form.cleaned_data.get('exchange')
			broker = form.cleaned_data.get('broker')
			if order_type != 'All':
				oldorder = oldorder.filter(order_type=order_type)
				formog.fields['order_type'].initial = order_type
			if sortfield != 'None':
				oldorder = oldorder.order_by(sortfield)
				formog.fields['sortfield'].initial = sortfield
			if ticker != '':
				oldorder = oldorder.filter(sid__ticker__icontains=ticker)
			if exchange != '':
				oldorder = oldorder.filter(eid__name__icontains=exchange)
			if broker != '':
				oldorder = oldorder.filter(bid__bid__name__icontains=broker)

	context = {'oldorders': oldorder.all(), 'form': formog}
	return render(request, 'client/past_order.html', context)


def wishlists_view(request):
	if check_user(request):
		return HttpResponseRedirect('/home')
	if not request.user.is_authenticated:
		messages.error(request, 'Please login first.')
		return HttpResponseRedirect('/login')
	client = models.Client.objects.filter(username=request.user.username).first()
	assert client is not None
	msg=''
	stock_wish_id = check_type(request.GET.get('id', None), int)
	if stock_wish_id is not None:
		stock_wish = models.StockWishlist.objects.select_related('wish_id').filter(pk=stock_wish_id, wish_id__clid=client).first()
		if stock_wish is not None:
			wish = stock_wish.wish_id
			stock_wish.delete()
			messages.success(request, 'Wishlist entry deleted.')
			if not models.StockWishlist.objects.filter(wish_id=wish).exists():
				wish.delete()
				messages.success(request, 'Wishlist also deleted.')
		else:
			messages.error(request, 'You can\'t delete this wishlist entry.')
		return HttpResponseRedirect('wishlists')

	if request.method == 'POST':
		formdata = forms.WishlistForm(data=request.POST)
		if formdata.is_valid():
			wname = formdata.cleaned_data['wname']
			stock = formdata.cleaned_data['stock']
			wish = models.Wishlist.objects.filter(wname__iexact=wname, clid=client).first()
			if wish is not None and stock is None:
				messages.error(request, 'Wishlist already exists')
				return HttpResponseRedirect('wishlists')
			if wish is None:
				wish = models.Wishlist(wname=wname, clid=client)
				wish.save()
				messages.success(request, 'Wishlist created.')
			if stock is not None:
				stock_wish = models.StockWishlist.objects.filter(wish_id=wish, sid=stock).first()
				if stock_wish is not None:
					print('kkkkk')
					messages.error(request, 'Stock is already present in the given wishlist.')
					resp=HttpResponseRedirect('wishlists')
					resp.set_cookie(key='msg',value='Stock is already present in the given wishlist.')
					return resp
				stock_wish = models.StockWishlist(wish_id=wish, sid=stock)
				stock_wish.save()
				msg='Stock added to wishlist'
				messages.success(request, 'Stock added to wishlist.')
	data = {}
	for wish in models.Wishlist.objects.all():
		data[wish.wname] = []
	stock_wishes = models.StockWishlist.objects.select_related('wish_id', 'sid').filter(wish_id__clid=client).order_by('wish_id__wname')
	for stock_wish in stock_wishes:
		wname = stock_wish.wish_id.wname
		data[wname].append((stock_wish, stock_wish.sid))
	form = forms.WishlistForm()
	context = {'data': data, 'form': form}
	resp= render(request, 'client/wishlists.html', context)
	resp.set_cookie(key='msg',value=msg if msg!='' else request.COOKIES.get('msg',''))
	return resp



