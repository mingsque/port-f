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

    def receive(self, text_data):
        print("???????????????????????????")

        event_massage = json.loads(text_data)
        no = event_massage['proxy_number']

        if event_massage['status'] == 'static':
            async_to_sync(self.channel_layer.group_send)('status', {'type': 'share_message',
                                                                    'message': {'target': 'static',
                                                                                'proxy_number': no,
                                                                                'status': 'static'}})
        else:
            async_to_sync(self.channel_layer.group_send)('status', {'type': 'share_message',
                                                                    'message': {'target': 'static',
                                                                                'proxy_number': no,
                                                                                'status': 'not_static'}})

    def share_message(self, event):
        print("!!!!!!")
        message = event['message']
        print(event)

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'target': message['target'],
            'status': message['status'],
            'no': str(message['proxy_number'])
        }))