from django.urls import path
from . import views

urlpatterns = [
    path('', views.selecionar_fila, name='selecionar_fila'),
    path('emitir/', views.emitir_senha, name='emitir_senha'),
    path('acompanhar/<int:senha_id>/', views.acompanhar_senha, name='acompanhar_senha'),
    path('atendente/', views.painel_atendente, name='painel_atendente'),
    path('chamar/', views.chamar_senha, name='chamar_senha'),
]