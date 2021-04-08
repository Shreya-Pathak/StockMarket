from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='broker_index'),
    path('home', views.home_view, name='broker_home'),
    path('approve_order', views.approve_order_view, name='broker_approve_order'),
    path('past_order', views.past_order_view, name='broker_past_order'),
    path('withdraw', views.withdraw_view, name='broker_withdraw'),
    path('companies', views.companies_view, name='broker_companies'),
    path('add_funds', views.add_funds_view, name='broker_add_funds'),
    path('logout', views.logout_view, name='broker_logout'),
]