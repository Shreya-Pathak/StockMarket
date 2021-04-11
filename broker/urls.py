from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='broker_index'),
    path('home', views.home_view, name='broker_home'),
    path('approve_order', views.approve_order_view, name='broker_approve_order'),
    path('past_order', views.past_order_view, name='broker_past_order'),
    path('logout', views.logout_view, name='broker_logout'),
]