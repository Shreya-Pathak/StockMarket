from dal import autocomplete
import market.models as models


def is_int(v):
    try:
        return int(v)
    except:
        return 0


class PortfolioAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Portfolio.objects.none()
        client = models.Client.objects.get(username=self.request.user.username)
        qs = models.Portfolio.objects.filter(clid=client, pname__icontains=self.q).order_by('pname')
        return qs


class StockAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Stock.objects.none()
        wish = self.forwarded.get('for_wishlist', None)
        if wish is not None:
            assert wish == 'for_wishlist'
            return models.Stock.objects.all()
        folio = self.forwarded.get('for_portfolio', None)
        if folio is not None:
            assert folio == 'for_portfolio'
            return models.Stock.objects.all()
        order_type = self.forwarded.get('order_type', False)
        quantity = is_int(self.forwarded.get('quantity', 0))
        folio_id = is_int(self.forwarded.get('portfolio', 0))
        if not order_type or not folio_id or quantity <= 0:
            return models.Stock.objects.none()
        if order_type == 'Buy':
            qs = models.Stock.objects.all()
        else:
            qs = models.Holdings.objects.filter(folio_id=folio_id)
            qs = qs.filter(quantity__gte=quantity)
            qs = models.Stock.objects.filter(sid__in=qs.values('sid'))
        qs = qs.filter(ticker__icontains=self.q).order_by('ticker')
        return qs


class ExchangeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Exchange.objects.none()
        sid = is_int(self.forwarded.get('stock', 0))
        if not sid:
            return models.Exchange.objects.none()
        qs = models.Exchange.objects.filter(eid__in=models.ListedAt.objects.filter(sid=sid).values('eid'))
        qs = qs.filter(name__icontains=self.q).order_by('name')
        return qs


class BrokerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Broker.objects.none()
        eid = is_int(self.forwarded.get('exchange', 0))
        if not eid:
            return models.Broker.objects.none()
        qs = models.Broker.objects.filter(bid__in=models.RegisteredAt.objects.filter(eid=eid).values('bid'))
        qs = qs.select_related('bid').filter(username__icontains=self.q).order_by('username')
        return qs