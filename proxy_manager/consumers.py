from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json


class StatusConsumer(WebsocketConsumer):

    def connect(self):

        async_to_sync(self.channel_layer.group_add)('status', self.channel_name)
        print(self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, event):

        print("!!!!!!!")
        message = event['message']

        data = {'message': message}

        self.send(json.dumps(data))

        #text_data_json = json.loads(text_data)
        #message = text_data_json['message']

    def share_message(self, event):
        message = event['message']

        status = message['listening_status']
        no = message['proxy_number']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'listening_status': status,
            'no': str(no)
        }))