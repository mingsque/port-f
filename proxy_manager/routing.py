from django.conf.urls import url

from .consumers import StatusConsumer

websocket_urlpatterns = [
    url('ws/status', StatusConsumer),
]