from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='broker_index'),
    path('signup', views.signup, name='broker_signup'),
]