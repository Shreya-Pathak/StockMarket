from django.urls import path

from . import views

urlpatterns = [
    path('stocklist', views.stockList, name='stocklist'),
    path('analysis/<str:tick>/<int:eid>', views.analysis, name='analysis'),
    path('65654index', views.index, name='index')
]