from django.urls import path

from . import views
from . import autocompletes

urlpatterns = [
    path('', views.index_view, name='client_index'),
    path('signup', views.signup_view, name='client_signup'),
    path('login', views.login_view, name='client_login'),
    path('home', views.home_view, name='client_home'),
    path('logout', views.logout_view, name='client_logout'),
    path('portfolio', views.portfolio_view, name='client_portfolio'),
    path('order', views.order_view, name='client_order'),

    path('stock-autocomplete', autocompletes.StockAutocomplete.as_view(), name='stock-autocomplete'),
    path('portfolio-autocomplete', autocompletes.PortfolioAutocomplete.as_view(), name='portfolio-autocomplete'),
    path('exchange-autocomplete', autocompletes.ExchangeAutocomplete.as_view(), name='exchange-autocomplete'),
    path('broker-autocomplete', autocompletes.BrokerAutocomplete.as_view(), name='broker-autocomplete'),
]