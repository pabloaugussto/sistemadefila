import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class FilaConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'fila_geral'

       
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

   
    def fila_update(self, event):
        message = event['message']

       
        self.send(text_data=json.dumps({
            'type': 'fila_update',
            'message': message
        }))
    