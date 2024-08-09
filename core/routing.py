from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/status/(?P<order_id>\d+)/$', consumers.DeliveryBoyLocationConsumer.as_asgi()),
]
