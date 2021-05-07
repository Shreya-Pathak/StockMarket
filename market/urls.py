from django.urls import path

from . import views
from . import autocompletes

urlpatterns = [
    path('', views.index_view, name='index'),
    path('stocklist/<int:page_num>', views.stocklist_view, name='stocklist'),
    path('analysis/<int:sid>/<int:eid>', views.analysis_view, name='analysis'),
    path('analysis/<int:sid>/<int:eid>/<str:start_date>/<str:end_date>', views.analysis_view, name='analysis'),
    path('analysis_ind/<int:iid>', views.analysis_view_index, name='analysis_ind'),
    path('analysis_ind/<int:iid>/<str:start_date>/<str:end_date>', views.analysis_view_index, name='analysis_ind'),
    path('companies/<int:cid>/<int:page_num>', views.companies_view, name='companies'),
    path('withdraw', views.withdraw_view, name='withdraw'),
    path('add_funds', views.add_funds_view, name='add_funds'),
    path('stock-autocomplete', autocompletes.StockAutocomplete.as_view(), name='stock-autocomplete'),
    path('exchange-autocomplete', autocompletes.ExchangeAutocomplete.as_view(), name='exchange-autocomplete'),
    path('index-autocomplete', autocompletes.IndexAutocomplete.as_view(), name='index-autocomplete'),
]