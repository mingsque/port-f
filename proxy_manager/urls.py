
from django.urls import path
from . import views


urlpatterns = [
    path('', views.login, name='login'),
    path('login', views.auth_using_slack, name='auth_using_slack'),
    path('main', views.login_action, name='login_action'),
    path('login', views.main, name='main'),
    path('proxy', views.proxy, name='proxy'),
    path('static_apply', views.static_apply, name='static_apply'),

]