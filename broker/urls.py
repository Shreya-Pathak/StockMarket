from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='broker_index'),
    path('signup', views.signup_view, name='broker_signup'),
    path('login', views.login_view, name='broker_login'),
    path('home', views.home_view, name='broker_home'),
    path('logout', views.logout_view, name='broker_logout'),
]