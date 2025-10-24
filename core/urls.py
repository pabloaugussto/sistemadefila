# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
# Se CustomAuthenticationForm não existir em forms.py, comente/remova a linha abaixo
from .forms import CustomAuthenticationForm
from . import views

urlpatterns = [
    # URLs de Autenticação
    path('', auth_views.LoginView.as_view(
            template_name='core/login.html',
            authentication_form=CustomAuthenticationForm
        ), name='login'),
    path('cadastro/', views.cadastro_paciente, name='cadastro'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # URLs do Fluxo do Paciente
    path('filas/', views.selecionar_fila, name='selecionar_fila'),
    path('emitir/', views.emitir_senha, name='emitir_senha'),
    path('acompanhar/<int:senha_id>/', views.acompanhar_senha, name='acompanhar_senha'),

    # URLs do Fluxo do Atendente
    path('atendente/', views.painel_atendente, name='painel_atendente'),
    # CORREÇÃO: Voltando o nome para 'chamar_senha' para consistência com o template
    path('atendente/chamar/', views.chamar_proxima_senha, name='chamar_senha'),
    path('atendente/iniciar/<int:senha_id>/', views.iniciar_atendimento, name='iniciar_atendimento'),
    path('atendente/finalizar/<int:senha_id>/', views.finalizar_atendimento, name='finalizar_atendimento'),
]