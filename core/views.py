# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.utils import timezone
# Importação atualizada para incluir PerfilAtendente
from .models import Fila, Senha, Paciente, Historico, PerfilAtendente
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib.auth import login
# Importação atualizada para incluir os novos forms de edição
from .forms import UserForm, PacienteForm, ObservacaoAtendimentoForm, UserEditForm, PerfilAtendenteForm 
from django.db.models import Count, Avg, F
from datetime import date
from django.db import transaction # Import para garantir que as alterações de perfil sejam atômicas


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
            
            # Notificação em tempo real
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
# FUNÇÕES DO ATENDENTE
# ==========================================================

@login_required 
def redirect_apos_login(request):
    if request.user.is_staff:
        return redirect('painel_atendente')
    else:
        return redirect('selecionar_fila')


@user_passes_test(is_staff)
def painel_atendente(request):
    filas = Fila.objects.all()
    senhas_aguardando = {}

    # Senhas que ESTE atendente está atendendo
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

    # Passo 1: Obter as filas que o atendente logado PODE atender (RF06/RF19)
    try:
        # Pega as filas que o atendente marcou no perfil. Se não marcou nenhuma, usa todas.
        filas_permitidas = request.user.perfil_atendente.filas_atendidas.all()
        if not filas_permitidas:
            filas_a_buscar = Fila.objects.all()
        else:
            filas_a_buscar = filas_permitidas
    except PerfilAtendente.DoesNotExist:
        # Caso o perfil ainda não exista no banco (o .get_or_create da view de perfil resolve isso)
        filas_a_buscar = Fila.objects.all()

    # Passo 2: Tenta buscar a próxima senha prioritária (P) dentro das filas permitidas
    fila_prioritaria = filas_a_buscar.filter(sigla='P').first()
    proxima_senha = None
    if fila_prioritaria:
        proxima_senha = Senha.objects.filter(fila=fila_prioritaria, status='AGU').order_by('data_emissao').first()

    # Passo 3: Se não houver prioritária, busca a próxima senha AGU em QUALQUER fila permitida
    if not proxima_senha:
        proxima_senha = Senha.objects.filter(fila__in=filas_a_buscar, status='AGU').order_by('data_emissao').first()

    if proxima_senha:
        proxima_senha.status = 'CHA'
        proxima_senha.atendente = request.user
        proxima_senha.hora_chamada = timezone.now()
        proxima_senha.save()

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


@user_passes_test(is_staff)
def iniciar_atendimento(request, senha_id):
    """Muda o status da senha chamada ('CHA') para 'Em Atendimento' ('ATE')."""
    senha = get_object_or_404(Senha, pk=senha_id)

    if senha.status in ['CHA', 'AGU']:
        senha.status = 'ATE'
        senha.atendente = request.user
        
        if not senha.hora_chamada:
             senha.hora_chamada = timezone.now()
             
        senha.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'fila_geral',
            {
                'type': 'fila_update',
                'message': f"ATE: {str(senha)}"
            }
        )

    return redirect('painel_atendente')

@user_passes_test(is_staff)
def finalizar_atendimento(request, senha_id):
    """Muda status para 'Finalizada' ('FIN'), salva observações e cria Histórico."""
    senha = get_object_or_404(Senha, pk=senha_id, atendente=request.user, status='ATE') 

    # Tenta obter a classe do formulário
    form_class = globals().get('ObservacaoAtendimentoForm')
    
    if request.method == 'POST':
        form = form_class(request.POST) if form_class else None 
        is_form_valid = form.is_valid() if form else True

        if is_form_valid:
            if form and hasattr(senha, 'observacoes'):
                senha.observacoes = form.cleaned_data['observacoes']

            hora_fim = timezone.now()
            if hasattr(senha, 'hora_fim_atendimento'):
                 senha.hora_fim_atendimento = hora_fim

            senha.status = 'FIN'
            senha.save()

            if senha.hora_chamada:
                 Historico.objects.create(
                     senha=senha,
                     atendente=request.user,
                     data_inicio_atendimento=senha.hora_chamada,
                 )

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
        if form_class:
            initial_obs = getattr(senha, 'observacoes', '') 
            form = form_class(initial={'observacoes': initial_obs})
        else:
            form = None 

    contexto = {
        'senha': senha,
        'form': form
    }
    return render(request, 'core/finalizar_atendimento.html', contexto)

# core/views.py

from django.shortcuts import render
from django.db.models import Avg, F, Count
from datetime import date
from .models import Historico, Fila # Certifique-se dos imports
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_staff)
def painel_relatorios(request):
    hoje = date.today()

    # Coleta segura dos parâmetros GET
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    # Conversão com fallback seguro
    try:
        data_inicio = date.fromisoformat(data_inicio_str) if data_inicio_str else hoje
    except ValueError:
        data_inicio = hoje

    try:
        data_fim = date.fromisoformat(data_fim_str) if data_fim_str else hoje
    except ValueError:
        data_fim = hoje

    # -------- FILTRO PRINCIPAL --------
    atendimentos_periodo = Historico.objects.filter(
        data_fim_atendimento__date__gte=data_inicio,
        data_fim_atendimento__date__lte=data_fim
    )

    # -------- MÉTRICAS GERAIS --------
    total_atendimentos = atendimentos_periodo.count()

    tempo_medio_segundos = atendimentos_periodo.aggregate(
        tempo_medio=Avg(F("data_fim_atendimento") - F("data_inicio_atendimento"))
    )["tempo_medio"]

    tempo_medio_minutos = (
        round(tempo_medio_segundos.total_seconds() / 60, 1)
        if tempo_medio_segundos else 0
    )

    # -------- ATENDIMENTOS POR FILA --------
    atendimentos_por_fila = atendimentos_periodo.values(
        "senha__fila__nome"
    ).annotate(
        total=Count("id")
    ).order_by("-total")

    todas_filas = Fila.objects.all()

    mapa_atendimentos = {
        item["senha__fila__nome"]: item["total"]
        for item in atendimentos_por_fila
    }

    relatorio_filas = [
        {
            "nome": fila.nome,
            "total": mapa_atendimentos.get(fila.nome, 0),
        }
        for fila in todas_filas
    ]

    # -------- LISTA DETALHADA --------
    lista_detalhada = atendimentos_periodo.order_by("-data_fim_atendimento")

    # -------- CONTEXTO FINAL --------
    contexto = {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "total_atendimentos": total_atendimentos,   # HTML usa esse nome
        "tempo_medio_minutos": tempo_medio_minutos,
        "relatorio_filas": relatorio_filas,
        "atendimentos_detalhados": lista_detalhada,
    }

    return render(request, "core/relatorios.html", contexto)


def cadastro_paciente(request):
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

# --- NOVO BLOCO: GERENCIAMENTO DE PERFIL ---
@login_required
def gerenciar_perfil(request):
    # Tenta obter o perfil do atendente, ou o cria se for a primeira vez
    perfil, created = PerfilAtendente.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        perfil_form = PerfilAtendenteForm(request.POST, instance=perfil)
        
        if user_form.is_valid() and perfil_form.is_valid():
            with transaction.atomic():
                user_form.save()
                perfil_form.save()
            return redirect('gerenciar_perfil')
    else:
        user_form = UserEditForm(instance=request.user)
        perfil_form = PerfilAtendenteForm(instance=perfil)
        
    contexto = {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'perfil': perfil,
    }
    return render(request, 'core/gerenciar_perfil.html', contexto)

def cancelar_senha_paciente(request, id):
    # Usamos get_object_or_404 por segurança. Se a senha não existir, dá erro 404 em vez de travar tudo.
    senha = get_object_or_404(Senha, id=id)
    
    # Atualiza o status
    senha.status = 'CAN' # Verifique se no seu model é 'C', 'CANCELADO' ou outro termo
    senha.save()
    
    # Redireciona para a tela de login/inicial
    # IMPORTANTE: Troque 'home' pelo 'name' da sua url principal no urls.py
    return redirect('login')