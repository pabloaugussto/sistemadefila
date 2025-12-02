from django.urls import re_path
from . import consumers
 
websocket_urlpatterns = [
    # CORRIGIDO: O caminho agora corresponde ao nome do grupo ('fila_geral')
    # que o seu views.py está usando para enviar as mensagens.
    re_path(r'^ws/fila_geral/$', consumers.FilaConsumer.as_asgi()),
]