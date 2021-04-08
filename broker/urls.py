from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='broker_index'),
    path('home', views.home_view, name='broker_home'),
    path('orders', views.order_view, name='broker_orders'),
    path('logout', views.logout_view, name='broker_logout'),
]