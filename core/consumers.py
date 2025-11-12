import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class FilaConsumer(WebsocketConsumer):
    def connect(self):
        # 1. Define o nome do grupo
        self.room_group_name = 'fila_geral'
        
        # 2. Adiciona o consumidor (o navegador) ao grupo 'fila_geral'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        # 3. Aceita a conexão WebSocket
        self.accept()

    def disconnect(self, close_code):
        # 1. Remove o consumidor do grupo
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # 2. Método que é chamado pelo views.py (via group_send)
    def fila_update(self, event):
        message = event['message']

        # 3. Envia a mensagem recebida de volta ao WebSocket do navegador
        self.send(text_data=json.dumps({
            'type': 'fila_update',
            'message': message
        }))