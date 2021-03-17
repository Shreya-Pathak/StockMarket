from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='client_index'),
    path('signup', views.signup_view, name='client_signup'),
    path('login', views.login_view, name='client_login'),
    path('home', views.home_view, name='client_home'),
    path('logout', views.logout_view, name='client_logout'),
    path('portfolio', views.portfolio_view, name='client_portfolio'),
    path('order', views.order_view, name='client_order'),
]