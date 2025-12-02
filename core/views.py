# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max, Avg, F, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import date
from django.db import transaction

from .models import Fila, Senha, Paciente, Historico, PerfilAtendente
from .forms import (
    UserForm,
    PacienteForm,
    ObservacaoAtendimentoForm,
    UserEditForm,
    PerfilAtendenteForm
)

# ========================================
# FUNÇÃO HELPER - SOMENTE STAFF
# ========================================

def is_staff(user):
    return user.is_staff


# ========================================
# PACIENTE - EMITIR E ACOMPANHAR
# ========================================

@login_required
def selecionar_fila(request):
    filas = Fila.objects.all()
    return render(request, 'core/selecionar_fila.html', {'filas': filas})


def emitir_senha(request):
    if request.user.is_authenticated and request.method == 'POST':
        fila_id = request.POST.get('fila_id')
        fila_selecionada = get_object_or_404(Fila, pk=fila_id)

        ultimo = Senha.objects.filter(fila=fila_selecionada).aggregate(
            Max('numero_senha')
        )['numero_senha__max']

        nova = Senha.objects.create(
            fila=fila_selecionada,
            numero_senha=(ultimo or 0) + 1,
            paciente=request.user
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'fila_geral',
            {'type': 'fila_update', 'message': f"EMITIDA: {str(nova)}"}
        )

        return redirect('acompanhar_senha', senha_id=nova.id)

    return redirect('selecionar_fila')


@login_required
def acompanhar_senha(request, senha_id):
    senha = get_object_or_404(Senha, pk=senha_id)
    posicao = (
        Senha.objects.filter(
            fila=senha.fila,
            status__in=['AGU', 'CHA', 'ATE'],
            data_emissao__lt=senha.data_emissao
        ).count() + 1
    )

    return render(
        request,
        'core/acompanhar_senha.html',
        {'senha': senha, 'posicao': posicao}
    )


# ========================================
# ATENDENTE
# ========================================

@login_required
def redirect_apos_login(request):
    return redirect('painel_atendente' if request.user.is_staff else 'selecionar_fila')


@user_passes_test(is_staff)
def painel_atendente(request):
    filas = Fila.objects.all()
    senhas_aguardando = {
        fila.nome: Senha.objects.filter(
            fila=fila, status__in=['AGU', 'CHA']
        ).order_by('data_emissao')
        for fila in filas
    }

    senhas_em_atendimento = Senha.objects.filter(
        status='ATE',
        atendente=request.user
    ).order_by('hora_chamada')

    return render(
        request,
        'core/painel_atendente.html',
        {
            'senhas_aguardando': senhas_aguardando,
            'senhas_em_atendimento': senhas_em_atendimento
        }
    )


@user_passes_test(is_staff)
def chamar_proxima_senha(request):

    try:
        filas_permitidas = request.user.perfil_atendente.filas_atendidas.all()
        filas_busca = filas_permitidas if filas_permitidas else Fila.objects.all()
    except PerfilAtendente.DoesNotExist:
        filas_busca = Fila.objects.all()

    fila_p = filas_busca.filter(sigla='P').first()
    proxima = None

    if fila_p:
        proxima = Senha.objects.filter(
            fila=fila_p, status='AGU'
        ).order_by('data_emissao').first()

    if not proxima:
        proxima = Senha.objects.filter(
            fila__in=filas_busca, status='AGU'
        ).order_by('data_emissao').first()

    if proxima:
        proxima.status = 'CHA'
        proxima.atendente = request.user
        proxima.hora_chamada = timezone.now()
        proxima.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'fila_geral',
            {'type': 'fila_update', 'message': f"CHAMADA: {str(proxima)}"}
        )

    return redirect('painel_atendente')


@user_passes_test(is_staff)
def iniciar_atendimento(request, senha_id):
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
            {'type': 'fila_update', 'message': f"ATE: {str(senha)}"}
        )

    return redirect('painel_atendente')


@user_passes_test(is_staff)
def finalizar_atendimento(request, senha_id):

    senha = get_object_or_404(
        Senha, pk=senha_id, atendente=request.user, status='ATE'
    )

    form_class = ObservacaoAtendimentoForm

    if request.method == 'POST':
        form = form_class(request.POST) if form_class else None

        if not form or form.is_valid():
            if form:
                senha.observacoes = form.cleaned_data['observacoes']

            hora_fim = timezone.now()
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
                {'type': 'fila_update', 'message': f"FINALIZADA: {str(senha)}"}
            )

            return redirect('painel_atendente')

    else:
        form = form_class(initial={'observacoes': getattr(senha, 'observacoes', '')})

    return render(
        request,
        'core/finalizar_atendimento.html',
        {'senha': senha, 'form': form}
    )


# ========================================
# RELATÓRIOS (VERSÃO MAIS NOVA)
# ========================================

@user_passes_test(lambda u: u.is_staff)
def painel_relatorios(request):

    hoje = date.today()

    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    try:
        data_inicio = date.fromisoformat(data_inicio_str) if data_inicio_str else hoje
    except:
        data_inicio = hoje

    try:
        data_fim = date.fromisoformat(data_fim_str) if data_fim_str else hoje
    except:
        data_fim = hoje

    atendimentos = Historico.objects.filter(
        data_fim_atendimento__date__gte=data_inicio,
        data_fim_atendimento__date__lte=data_fim
    )

    total_atendimentos = atendimentos.count()

    tempo_medio_segundos = atendimentos.aggregate(
        tempo_medio=Avg(F('data_fim_atendimento') - F('data_inicio_atendimento'))
    )['tempo_medio']

    tempo_medio_minutos = (
        round(tempo_medio_segundos.total_seconds() / 60, 1)
        if tempo_medio_segundos else 0
    )

    atendimentos_por_fila = atendimentos.values(
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
        {"nome": fila.nome, "total": mapa_atendimentos.get(fila.nome, 0)}
        for fila in todas_filas
    ]

    lista_detalhada = atendimentos.order_by("-data_fim_atendimento")

    return render(
        request,
        "core/relatorios.html",
        {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "total_atendimentos": total_atendimentos,
            "tempo_medio_minutos": tempo_medio_minutos,
            "relatorio_filas": relatorio_filas,
            "atendimentos_detalhados": lista_detalhada,
        }
    )


# ========================================
# CADASTRO DE PACIENTE
# ========================================

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

    return render(
        request,
        'core/cadastro.html',
        {'user_form': user_form, 'paciente_form': paciente_form}
    )


# ========================================
# GERENCIAR PERFIL DO ATENDENTE
# ========================================

@login_required
def gerenciar_perfil(request):
    perfil, _ = PerfilAtendente.objects.get_or_create(user=request.user)

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

    return render(
        request,
        'core/gerenciar_perfil.html',
        {'user_form': user_form, 'perfil_form': perfil_form, 'perfil': perfil}
    )


# ========================================
# CANCELAMENTO DE SENHA PELO PACIENTE
# ========================================

def cancelar_senha_paciente(request, id):
    senha = get_object_or_404(Senha, id=id)
    senha.status = 'CAN'
    senha.save()
    return redirect('login')
