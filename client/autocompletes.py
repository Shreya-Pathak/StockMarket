from dal import autocomplete
import market.models as models


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
        order_type = self.forwarded.get('order_type', False)
        quantity = int(self.forwarded.get('quantity', 0))
        folio_id = int(self.forwarded.get('portfolio', 0))
        if not order_type or not folio_id or quantity <= 0:
            return models.Stock.objects.none()
        qs = models.Holdings.objects.filter(folio_id=folio_id)
        if order_type == 'Sell':
            qs = qs.filter(quantity__gte=quantity)
        qs = models.Stock.objects.filter(sid__in=qs.values('sid'))
        qs = qs.filter(ticker__icontains=self.q).order_by('ticker')
        return qs


class ExchangeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Exchange.objects.none()
        sid = int(self.forwarded.get('stock', 0))
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
        eid = int(self.forwarded.get('exchange', 0))
        if not eid:
            return models.Broker.objects.none()
        qs = models.Broker.objects.filter(bid__in=models.RegisteredAt.objects.filter(eid=eid).values('bid'))
        qs = qs.select_related('bid').filter(username__icontains=self.q).order_by('username')
        return qs