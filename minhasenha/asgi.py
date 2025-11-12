import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import core.routing # Importa o arquivo de rotas do seu app 'core'

# CORRIGIDO: A variável de ambiente aponta para o nome do projeto 'minhasenha'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minhasenha.settings') 

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            core.routing.websocket_urlpatterns
        )
    ),
})