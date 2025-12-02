# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import CustomAuthenticationForm 
from . import views

urlpatterns = [
    # --- LOGIN DO PACIENTE (na raiz '/') ---
    path('', auth_views.LoginView.as_view(
            template_name='core/login.html', 
            authentication_form=CustomAuthenticationForm 
        ), name='login'), 

    # --- NOVO LOGIN DO ATENDENTE ---
    path('atendente/login/', auth_views.LoginView.as_view(
            template_name='core/atendente_login.html' 
        ), name='atendente_login'), 

    path('redirect/', views.redirect_apos_login, name='redirect_apos_login'),
    path('relatorios/', views.painel_relatorios, name='painel_relatorios'),

    # --- URL DE PERFIL (NOVA) ---
    path('perfil/', views.gerenciar_perfil, name='gerenciar_perfil'),

    # --- OUTRAS URLS ---
    path('cadastro/', views.cadastro_paciente, name='cadastro'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('filas/', views.selecionar_fila, name='selecionar_fila'),
    path('emitir/', views.emitir_senha, name='emitir_senha'),
    path('acompanhar/<int:senha_id>/', views.acompanhar_senha, name='acompanhar_senha'),
    path('atendente/', views.painel_atendente, name='painel_atendente'),
    path('atendente/chamar/', views.chamar_proxima_senha, name='chamar_senha'),
    path('atendente/iniciar/<int:senha_id>/', views.iniciar_atendimento, name='iniciar_atendimento'),
    path('atendente/finalizar/<int:senha_id>/', views.finalizar_atendimento, name='finalizar_atendimento'),
    path('cancelar-paciente/<int:id>/', views.cancelar_senha_paciente, name='cancelar_senha_paciente'),
]