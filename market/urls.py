from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    
    path('stocklist/<int:client>', views.stocklist_view, name='stocklist'),
    path('analysis/<int:sid>/<int:eid>/<int:client>', views.analysis_view, name='analysis'),
]