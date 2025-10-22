from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.utils import timezone 
from .models import Fila, Senha, Paciente 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import UserForm, PacienteForm
from .forms import ObservacaoAtendimentoForm 


# ==========================================================
# FUNÇÕES DO PACIENTE (EMITIR E ACOMPANHAR) 
# Mantido o seu bloco de comentários para organização (HEAD)
# ==========================================================

@login_required
def selecionar_fila(request):
    filas = Fila.objects.all()
    contexto = {'filas': filas}
    return render(request, 'core/selecionar_fila.html', contexto)


def emitir_senha(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            fila_id = request.POST.get('fila_id')
            fila_selecionada = get_object_or_404(Fila, pk=fila_id)
            
            ultimo_numero = Senha.objects.filter(fila=fila_selecionada).aggregate(Max('numero_senha'))['numero_senha__max']
            proximo_numero = (ultimo_numero or 0) + 1

            nova_senha = Senha.objects.create(
                fila=fila_selecionada,
                numero_senha=proximo_numero,
                paciente=request.user 
            )
            
            # Notificação em tempo real (RF16)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'fila_geral',
                {
                    'type': 'fila_update',
                    'message': f"EMITIDA: {str(nova_senha)}"
                }
            )
            
            return redirect('acompanhar_senha', senha_id=nova_senha.id)

    return redirect('selecionar_fila')


@login_required
def acompanhar_senha(request, senha_id):
    senha = get_object_or_404(Senha, pk=senha_id)
    posicao = Senha.objects.filter(
        fila=senha.fila, 
        status__in=['AGU', 'CHA', 'ATE'], 
        data_emissao__lt=senha.data_emissao
    ).count() + 1
    
    contexto = {
        'senha': senha,
        'posicao': posicao
    }
    return render(request, 'core/acompanhar_senha.html', contexto)


# ==========================================================
# FUNÇÕES DO ATENDENTE (RF15 e RF17)
# ==========================================================

@login_required
def painel_atendente(request):
    filas = Fila.objects.all()
    senhas_aguardando = {}
    
    # Senhas que este atendente está atualmente atendendo (HEAD)
    senhas_em_atendimento = Senha.objects.filter(status='ATE', atendente=request.user).order_by('hora_inicio_atendimento')

    for fila in filas:
        # Senhas aguardando ou já chamadas (HEAD - Lógica correta)
        senhas_aguardando[fila.nome] = Senha.objects.filter(fila=fila, status__in=['AGU', 'CHA']).order_by('data_emissao')

    contexto = {
        'senhas_aguardando': senhas_aguardando,
        'senhas_em_atendimento': senhas_em_atendimento # Variável correta usada no template
    }
    return render(request, 'core/painel_atendente.html', contexto)


@login_required
def chamar_proxima_senha(request): 
    """RF15: Chamada de Próxima Senha Automática (Lógica de Prioridade).""" 
    
    # 1. Tenta buscar a próxima senha prioritária
    fila_prioritaria = Fila.objects.filter(sigla='P').first()
    proxima_senha = None
    if fila_prioritaria:
        proxima_senha = Senha.objects.filter(fila=fila_prioritaria, status='AGU').order_by('data_emissao').first()

    # 2. Se não houver prioritária, busca a próxima geral
    if not proxima_senha:
        proxima_senha = Senha.objects.filter(status='AGU').order_by('data_emissao').first()

    if proxima_senha:
        proxima_senha.status = 'CHA'
        proxima_senha.atendente = request.user 
        proxima_senha.hora_chamada = timezone.now()
        proxima_senha.save()

        # Notificação em tempo real (RF16)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'fila_geral',
            {
                'type': 'fila_update',
                'message': f"CHAMADA: {str(proxima_senha)}" 
            }
        )

    return redirect('painel_atendente') 


@login_required
def iniciar_atendimento(request, senha_id):
    """Muda o status para Em Atendimento e registra o tempo inicial (RF15)."""
    senha = get_object_or_404(Senha, pk=senha_id)
    
    if senha.status in ['CHA', 'AGU']:
        senha.status = 'ATE' 
        senha.atendente = request.user 
        senha.hora_inicio_atendimento = timezone.now()
        senha.save()
        
    return redirect('painel_atendente') 


@login_required
def finalizar_atendimento(request, senha_id):
    """Registra a conclusão, tempo final e observações (RF17)."""
    # Mantido o seu código completo (HEAD)
    senha = get_object_or_404(Senha, pk=senha_id, atendente=request.user) 
    
    if request.method == 'POST':
        form = ObservacaoAtendimentoForm(request.POST) 
        
        if form.is_valid():
            senha.observacoes = form.cleaned_data['observacoes'] 
            senha.hora_fim_atendimento = timezone.now() 
            senha.status = 'FIN' 
            senha.save()
            
            # Notificação em tempo real (RF16)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'fila_geral',
                {
                    'type': 'fila_update',
                    'message': f"FINALIZADA: {str(senha)}" 
                }
            )

            return redirect('painel_atendente') 
            
    else:
        form = ObservacaoAtendimentoForm(initial={'observacoes': senha.observacoes})

    contexto = {
        'senha': senha,
        'form': form
    }
    # Caminho do template simplificado para evitar TemplateDoesNotExist
    return render(request, 'finalizar_atendimento.html', contexto) 
    
# ==========================================================
# FUNÇÕES DE AUTENTICAÇÃO 
# ==========================================================

def cadastro_paciente(request):
    """RF12: Permite que um novo usuário se registre como paciente."""
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        paciente_form = PacienteForm(request.POST)
        if user_form.is_valid() and paciente_form.is_valid():
            user = user_form.save(commit=False)
            user.username = paciente_form.cleaned_data['cpf']
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            paciente = paciente_form.save(commit=False)
            paciente.user = user
            paciente.save()

            login(request, user)
            return redirect('selecionar_fila')
    else:
        user_form = UserForm()
        paciente_form = PacienteForm()
    
    contexto = {
        'user_form': user_form,
        'paciente_form': paciente_form
    }
    return render(request, 'core/cadastro.html', contexto)

# A função 'finalizar_atendimento' duplicada no final (do commit remoto) foi removida.