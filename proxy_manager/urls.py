
from django.urls import path
from . import views

urlpatterns = [
    path('', views.Login.login, name='login'),
    path('admin_login', views.admin_login, name='admin_login'),
    path('auth', views.Login.auth_using_slack, name='auth_using_slack'),
    path('main', views.main, name='main'),
    path('proxy', views.proxy, name='proxy'),
    path('apply', views.static_apply_form, name='static_apply_form'),
    path('submit', views.static_apply_submit, name='static_apply_submit'),
    path('status', views.static_status, name='static_status'),
    path('apply_list', views.static_apply_list, name='static_apply_list'),
    path('apply_ok', views.apply_ok, name='apply_ok'),
    path('del_proxy', views.del_proxy, name='del_proxy'),
    path('apply_reject', views.apply_reject, name='apply_reject'),
    path('admin_login_action', views.admin_login_action, name='admin_login_action'),
    path('node_proxy_list', views.node_proxy_list, name='node_proxy_list'),
    path('node_proxy_forward', views.node_proxy_forward, name='node_proxy_forward'),
    path('node_proxy_close', views.node_proxy_close, name='node_proxy_close'),
    path('timer_cancel', views.timer_cancel, name='timer_cancel'),
    path('timer_on', views.timer_on, name='timer_on'),

]

