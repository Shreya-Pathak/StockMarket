from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('client_signup', views.clientsignup, name='clientsignup'),
    path('broker_signup', views.brokersignup, name='brokersignup'),
    path('stocklist', views.stockList, name='stocklist'),
    path('analysis/<str:tick>/<int:eid>',views.analysis,name='analysis'),
]