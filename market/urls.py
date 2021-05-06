from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('stocklist/<int:page_num>', views.stocklist_view, name='stocklist'),
    path('analysis/<int:sid>/<int:eid>', views.analysis_view, name='analysis'),
    path('analysis_ind/<int:iid>', views.analysis_view_index, name='analysis_ind'),
    path('companies/<int:cid>/<int:page_num>', views.companies_view, name='companies'),
    path('withdraw', views.withdraw_view, name='withdraw'),
    path('add_funds', views.add_funds_view, name='add_funds'),
]