from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='client_index'),
    path('signup', views.signup, name='client_signup'),
]