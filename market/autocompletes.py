from dal import autocomplete
import market.models as models


def is_int(v):
    try:
        return int(v)
    except:
        return 0


class StockAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Stock.objects.none()
        qs = models.Stock.objects.all()
        qs = qs.filter(ticker__icontains=self.q).order_by('ticker')
        return qs

class IndexAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return models.Indices.objects.none()
        qs = models.Indices.objects.all()
        qs = qs.filter(index_name__icontains=self.q).order_by('index_name')
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
