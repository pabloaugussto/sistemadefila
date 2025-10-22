# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
# ATENÇÃO: Se o CustomAuthenticationForm não existe em forms.py, 
# REMOVA a linha abaixo. Vou assumir que ele será criado/corrigido.
from .forms import CustomAuthenticationForm 
from . import views

urlpatterns = [
    # URLs de Autenticação
    # Mescla: Manter a URL raiz ('') usando a forma de autenticação personalizada (remote)
    path('', auth_views.LoginView.as_view(
        template_name='core/login.html',
        authentication_form=CustomAuthenticationForm # Adicionado do commit remoto
    ), name='login'),
    
    # URL do Paciente e Logout (sem conflitos)
    path('cadastro/', views.cadastro_paciente, name='cadastro'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # URLs do Paciente (sem conflitos)
    path('filas/', views.selecionar_fila, name='selecionar_fila'),
    path('emitir/', views.emitir_senha, name='emitir_senha'),
    path('acompanhar/<int:senha_id>/', views.acompanhar_senha, name='acompanhar_senha'),
    
    # URL do Painel do Atendente (sem conflitos)
    path('atendente/', views.painel_atendente, name='painel_atendente'),

    # ROTAS DO ATENDENTE (Corrigido e Mantido do seu HEAD)
    path('atendente/chamar/', views.chamar_proxima_senha, name='chamar'), # NOME CORRIGIDO/SIMPLIFICADO
    path('atendente/iniciar/<int:senha_id>/', views.iniciar_atendimento, name='iniciar_atendimento'),
    
    # Rotas de Finalização
    # Mescla: Manter o caminho completo ('atendente/finalizar/') da sua versão HEAD para organização.
    # O nome da URL 'finalizar_atendimento' é usado corretamente no painel_atendente.html.
    path('atendente/finalizar/<int:senha_id>/', views.finalizar_atendimento, name='finalizar_atendimento'),
]