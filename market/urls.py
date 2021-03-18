from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    
    path('stocklist/<int:client>/<int:st>/', views.stocklist_view, name='stocklist'),
    path('analysis/<int:sid>/<int:eid>', views.analysis_view, name='analysis'),
]