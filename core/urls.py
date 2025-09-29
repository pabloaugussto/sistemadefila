from django.urls import path
from . import views

urlpatterns = [
    # URL da página de seleção de fila
    path('', views.selecionar_fila, name='selecionar_fila'),
    
    # URL que o formulário usará para emitir a senha
    path('emitir/', views.emitir_senha, name='emitir_senha'),
]