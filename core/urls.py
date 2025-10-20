from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # URLs de Autenticação
    path('', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('cadastro/', views.cadastro_paciente, name='cadastro'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # URLs do Paciente
    path('filas/', views.selecionar_fila, name='selecionar_fila'),
    path('emitir/', views.emitir_senha, name='emitir_senha'),
    path('acompanhar/<int:senha_id>/', views.acompanhar_senha, name='acompanhar_senha'),
    
    # URL do Painel do Atendente
    path('atendente/', views.painel_atendente, name='painel_atendente'),

    # ROTAS DO ATENDENTE (RF15 e RF17)
    path('atendente/chamar/', views.chamar_proxima_senha, name='chamar'), # NOME SIMPLIFICADO AQUI
    path('atendente/iniciar/<int:senha_id>/', views.iniciar_atendimento, name='iniciar_atendimento'),
    path('atendente/finalizar/<int:senha_id>/', views.finalizar_atendimento, name='finalizar_atendimento'),
]