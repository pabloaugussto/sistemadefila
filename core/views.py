from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.utils import timezone
from .models import Fila, Senha, Paciente, Historico 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib.auth import login
from .forms import UserForm, PacienteForm, ObservacaoAtendimentoForm # Importa o formulário de observações
from django.db.models import Count, Avg, F # Para estatísticas
from datetime import date # Para filtrar por data


# Função helper para checar se é staff 
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

@login_required # Garante que só usuários logados acessem
def redirect_apos_login(request):
    if request.user.is_staff:
        # Se for atendente/admin, vai para o painel
        return redirect('painel_atendente')
    else:
        # Se for paciente, vai para a seleção de filas
        return redirect('selecionar_fila')


@user_passes_test(is_staff)
def painel_atendente(request):
    filas = Fila.objects.all()
    senhas_aguardando = {}

    # CORREÇÃO AQUI: Usar 'hora_chamada' para ordenar
    senhas_em_atendimento = Senha.objects.filter(status='ATE', atendente=request.user).order_by('hora_chamada')

    for fila in filas:
        senhas_aguardando[fila.nome] = Senha.objects.filter(fila=fila, status__in=['AGU', 'CHA']).order_by('data_emissao')

    contexto = {
        'senhas_aguardando': senhas_aguardando,
        'senhas_em_atendimento': senhas_em_atendimento
    }
    return render(request, 'core/painel_atendente.html', contexto)

@user_passes_test(is_staff)
def chamar_proxima_senha(request):
    """Chama a próxima senha (prioritária primeiro) e muda status para 'CHA'."""

    fila_prioritaria = Fila.objects.filter(sigla='P').first()
    proxima_senha = None
    if fila_prioritaria:
        proxima_senha = Senha.objects.filter(fila=fila_prioritaria, status='AGU').order_by('data_emissao').first()

    if not proxima_senha:
        proxima_senha = Senha.objects.filter(status='AGU').order_by('data_emissao').first()

    if proxima_senha:
        proxima_senha.status = 'CHA'
        proxima_senha.atendente = request.user
        # --- VERIFIQUE ESTAS DUAS LINHAS COM MUITA ATENÇÃO ---
        proxima_senha.hora_chamada = timezone.now() # Define a hora atual
        proxima_senha.save()                       # Salva a alteração no banco
        # ---------------------------------------------------

        # Notificação em tempo real
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

@user_passes_test(is_staff)
def finalizar_atendimento(request, senha_id):
    """Muda status para 'Finalizada' ('FIN'), salva observações e cria Histórico."""
    # Garante que só finalize o que está atendendo (status='ATE') e pertence ao atendente
    senha = get_object_or_404(Senha, pk=senha_id, atendente=request.user, status='ATE') 

    # Verifica se o form de observação existe
    form_class = ObservacaoAtendimentoForm if 'ObservacaoAtendimentoForm' in globals() and ObservacaoAtendimentoForm else None

    if request.method == 'POST':
        # Processa o formulário apenas se ele existir
        form = form_class(request.POST) if form_class else None 
        
        # Validação do formulário (se ele existir)
        is_form_valid = form.is_valid() if form else True # Se não há form, considera válido

        if is_form_valid:
            # Salva observações se o campo e o form existirem
            if form and hasattr(senha, 'observacoes'):
                 senha.observacoes = form.cleaned_data['observacoes']

            hora_fim = timezone.now()
            # Salva hora_fim se o campo existir
            if hasattr(senha, 'hora_fim_atendimento'):
                 senha.hora_fim_atendimento = hora_fim

            senha.status = 'FIN'
            senha.save()

            # --- Criação do Histórico (CORRIGIDO) ---
            # Verifica se hora_chamada existe antes de criar o histórico
            if senha.hora_chamada: # <-- USA hora_chamada
                 Historico.objects.create(
                     senha=senha,
                     atendente=request.user,
                     # Usa hora_chamada como início
                     data_inicio_atendimento=senha.hora_chamada, # <-- USA hora_chamada
                 )
            # --- Fim Histórico ---

            # Notificação em tempo real
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'fila_geral',
                {
                    'type': 'fila_update',
                    'message': f"FINALIZADA: {str(senha)}"
                }
            )

            # Redireciona de volta ao painel
            return redirect('painel_atendente')
            
    # Lógica para GET (exibir o form, se existir)
    else: 
        if form_class:
            initial_obs = getattr(senha, 'observacoes', '') 
            form = form_class(initial={'observacoes': initial_obs})
        else:
            form = None 

    contexto = {
        'senha': senha,
        'form': form
    }
    # Renderiza o template de finalização (assumindo que existe)
    return render(request, 'core/finalizar_atendimento.html', contexto)
# ==========================================================
# FUNÇÕES DE AUTENTICAÇÃO
# ==========================================================

@user_passes_test(is_staff)
def painel_relatorios(request):
    hoje = date.today()

    # Busca todos os atendimentos finalizados hoje
    atendimentos_hoje = Historico.objects.filter(data_fim_atendimento__date=hoje)

    # --- Estatísticas Gerais (Como estava) ---
    total_atendimentos_hoje = atendimentos_hoje.count()
    tempo_medio_segundos = atendimentos_hoje.aggregate(
        tempo_medio=Avg(F('data_fim_atendimento') - F('data_inicio_atendimento'))
    )['tempo_medio']
    tempo_medio_minutos = round(tempo_medio_segundos.total_seconds() / 60, 1) if tempo_medio_segundos else 0

    # --- LÓGICA PARA A LISTA (Voltando ao que era) ---
    atendimentos_por_fila = atendimentos_hoje.values(
        'senha__fila__nome' # O campo que queremos agrupar
    ).annotate(
        total=Count('id') # Conta quantos IDs tem em cada grupo
    ).order_by('-total') # Ordena

    todas_filas = Fila.objects.all()
    relatorio_filas = []
    mapa_atendimentos = {item['senha__fila__nome']: item['total'] for item in atendimentos_por_fila}

    for fila in todas_filas:
        relatorio_filas.append({
            'nome': fila.nome,
            'total': mapa_atendimentos.get(fila.nome, 0)
        })
    # --- FIM DA LÓGICA DA LISTA ---

    contexto = {
        'data_hoje': hoje,
        'total_atendimentos_hoje': total_atendimentos_hoje,
        'tempo_medio_minutos': tempo_medio_minutos,
        'relatorio_filas': relatorio_filas, # <-- Enviando a lista para o template
    }
    
    return render(request, 'core/relatorios.html', contexto)

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
