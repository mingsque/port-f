
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('main', views.main, name='main'),
    path('auth', views.auth_using_slack, name='auth_using_slack'),
    path('main', views.login_action, name='login_action'),
    path('proxy', views.proxy, name='proxy'),
    path('apply', views.static_apply_form, name='static_apply_form'),
    path('submit', views.static_apply_submit, name='static_apply_submit'),
    path('status', views.static_status, name='static_status'),
    path('apply_list', views.static_apply_list, name='static_apply_list'),
    path('apply_ok', views.apply_ok, name='apply_ok'),
    path('del_proxy', views.del_proxy, name='del_proxy'),
]