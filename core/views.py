from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.utils import timezone
from .models import Fila, Senha, Paciente, Historico # Importamos tudo
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required, user_passes_test # Importamos ambos
from django.contrib.auth import login
from .forms import UserForm, PacienteForm, ObservacaoAtendimentoForm # Importamos todos os forms

# Função helper para checar se é staff (Mantida da sua versão)
def is_staff(user):
    return user.is_staff

# ==========================================================
# FUNÇÕES DO PACIENTE (EMITIR E ACOMPANHAR)
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
            
            # Notificação em tempo real (Mantida da versão da colega - mais descritiva)
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
    # Lógica de posição da versão da colega (mais robusta)
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
# FUNÇÕES DO ATENDENTE
# ==========================================================

@user_passes_test(is_staff) # Decorator da sua versão (mais seguro)
def painel_atendente(request):
    filas = Fila.objects.all()
    senhas_aguardando = {}
    
    # Lógica da versão da colega (com status 'ATE')
    senhas_em_atendimento = Senha.objects.filter(status='ATE', atendente=request.user).order_by('data_chamada') # Assumindo data_chamada como início

    for fila in filas:
        senhas_aguardando[fila.nome] = Senha.objects.filter(fila=fila, status__in=['AGU', 'CHA']).order_by('data_emissao')

    contexto = {
        'senhas_aguardando': senhas_aguardando,
        'senhas_em_atendimento': senhas_em_atendimento
    }
    return render(request, 'core/painel_atendente.html', contexto)

@user_passes_test(is_staff) # Decorator da sua versão
def chamar_proxima_senha(request): # Nome e docstring da versão da colega
    """RF15: Chamada de Próxima Senha Automática (Lógica de Prioridade)."""
    
    fila_prioritaria = Fila.objects.filter(sigla='P').first()
    proxima_senha = None
    if fila_prioritaria:
        proxima_senha = Senha.objects.filter(fila=fila_prioritaria, status='AGU').order_by('data_emissao').first()

    if not proxima_senha:
        proxima_senha = Senha.objects.filter(status='AGU').order_by('data_emissao').first()

    if proxima_senha:
        proxima_senha.status = 'CHA'
        # Lógica da versão da colega
        proxima_senha.atendente = request.user
        proxima_senha.data_chamada = timezone.now() # Usando o nome do seu campo, mas com a lógica dela
        proxima_senha.save()

        # Notificação em tempo real (Versão da colega)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'fila_geral',
            {
                'type': 'fila_update',
                'message': f"CHAMADA: {str(proxima_senha)}"
            }
        )

    return redirect('painel_atendente')

@user_passes_test(is_staff) # Adicionado decorator seguro
def iniciar_atendimento(request, senha_id):
    """Muda o status para Em Atendimento e registra o tempo inicial (RF15)."""
    senha = get_object_or_404(Senha, pk=senha_id)
    
    # Verifica se a senha está aguardando ou já foi chamada
    if senha.status in ['CHA', 'AGU']:
        senha.status = 'ATE' # Novo status 'Em Atendimento'
        senha.atendente = request.user
        # Precisamos de um campo para hora_inicio_atendimento no models.Senha
        # Vamos assumir que data_chamada serve para isso por enquanto
        # senha.hora_inicio_atendimento = timezone.now() # Idealmente seria um campo novo
        senha.save()
        
    return redirect('painel_atendente')

@user_passes_test(is_staff) # Decorator da sua versão
def finalizar_atendimento(request, senha_id):
    """Registra a conclusão, tempo final, observações e cria histórico (RF17)."""
    # Lógica de busca da versão da colega
    senha = get_object_or_404(Senha, pk=senha_id, atendente=request.user)
    
    if request.method == 'POST':
        form = ObservacaoAtendimentoForm(request.POST)
        
        if form.is_valid():
            senha.observacoes = form.cleaned_data['observacoes'] # Campo novo da colega
            # Precisamos de um campo hora_fim_atendimento no models.Senha
            # Vamos usar timezone.now() por enquanto
            hora_fim = timezone.now()
            # senha.hora_fim_atendimento = hora_fim # Idealmente seria um campo novo
            senha.status = 'FIN'
            senha.save()
            
            # --- Criação do Histórico (Lógica da sua versão, adaptada) ---
            if senha.data_chamada: # Usando o campo que você criou
                 Historico.objects.create(
                     senha=senha,
                     atendente=request.user,
                     data_inicio_atendimento=senha.data_chamada,
                     # O modelo Historico já salva data_fim_atendimento automaticamente
                 )
            # --- Fim Histórico ---

            # Notificação em tempo real (Versão da colega)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'fila_geral',
                {
                    'type': 'fila_update',
                    'message': f"FINALIZADA: {str(senha)}"
                }
            )

            # Redireciona de volta ao painel (Lógica da sua versão)
            return redirect('painel_atendente')
            
    else:
        # Lógica GET da versão da colega
        form = ObservacaoAtendimentoForm(initial={'observacoes': getattr(senha, 'observacoes', '')}) # Usando getattr para segurança

    contexto = {
        'senha': senha,
        'form': form
    }
    # Mantendo a renderização do template da colega para o GET
    return render(request, 'core/finalizar_atendimento.html', contexto) # Assumindo que o template existe

# ==========================================================
# FUNÇÕES DE AUTENTICAÇÃO
# ==========================================================

def cadastro_paciente(request):
    # (Conteúdo idêntico, mantido)
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
