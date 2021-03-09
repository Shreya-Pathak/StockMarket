from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('client_signup', views.clientsignup, name='clientsignup'),
]