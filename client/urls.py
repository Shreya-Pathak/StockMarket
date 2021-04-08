from django.urls import path

from . import views
from . import autocompletes

urlpatterns = [
    path('', views.index_view, name='client_index'),
    path('home', views.home_view, name='client_home'),
    path('logout', views.logout_view, name='client_logout'),
    path('wishlists', views.wishlists_view, name='client_wishlists'),
    path('companies', views.companies_view, name='client_companies'),
    path('portfolio', views.portfolio_view, name='client_portfolio'),
    path('place_order', views.place_order_view, name='client_place_order'),
    path('past_order', views.past_order_view, name='client_past_order'),
    path('cancel_order', views.cancel_order_view, name='client_cancel_order'),
    path('withdraw', views.withdraw_view, name='client_withdraw'),
    path('add_funds', views.add_funds_view, name='client_add_funds'),
    path('stock-autocomplete', autocompletes.StockAutocomplete.as_view(), name='stock-autocomplete'),
    path('portfolio-autocomplete', autocompletes.PortfolioAutocomplete.as_view(), name='portfolio-autocomplete'),
    path('exchange-autocomplete', autocompletes.ExchangeAutocomplete.as_view(), name='exchange-autocomplete'),
    path('broker-autocomplete', autocompletes.BrokerAutocomplete.as_view(), name='broker-autocomplete'),
]