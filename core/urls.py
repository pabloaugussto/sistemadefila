from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # URL para a página de login
    path('', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    
    # URL para cadastro de novos pacientes
    path('cadastro/', views.cadastro_paciente, name='cadastro'),
    
    # URL para logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
   # URLs do sistema de filas
    path('filas/', views.selecionar_fila, name='selecionar_fila'),
    path('emitir/', views.emitir_senha, name='emitir_senha'),
    path('acompanhar/<int:senha_id>/', views.acompanhar_senha, name='acompanhar_senha'),
    path('atendente/', views.painel_atendente, name='painel_atendente'),
    path('chamar/', views.chamar_senha, name='chamar_senha'),
]