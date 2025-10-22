from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from .models import Fila, Senha, Paciente, Historico 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from .forms import UserForm, PacienteForm
from django.utils import timezone

def is_staff(user):
    return user.is_staff


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
            
            return redirect('acompanhar_senha', senha_id=nova_senha.id)

    return redirect('selecionar_fila')


@login_required
def acompanhar_senha(request, senha_id):
    senha = get_object_or_404(Senha, pk=senha_id)
    posicao = Senha.objects.filter(
        fila=senha.fila, 
        status='AGU', 
        id__lt=senha.id
    ).count() + 1
    
    contexto = {
        'senha': senha,
        'posicao': posicao
    }
    return render(request, 'core/acompanhar_senha.html', contexto)


@user_passes_test(is_staff)
def painel_atendente(request):
    filas = Fila.objects.all()
    senhas_aguardando = {}
    for fila in filas:
        senhas_aguardando[fila.nome] = Senha.objects.filter(fila=fila, status='AGU').order_by('data_emissao')
    senha_em_atendimento = Senha.objects.filter(status='CHA').order_by('-data_emissao').first()

    contexto = {
        'senhas_aguardando': senhas_aguardando,
        'senha_em_atendimento': senha_em_atendimento,
    }
    return render(request, 'core/painel_atendente.html', contexto)


@user_passes_test(is_staff)
def chamar_senha(request):
    fila_prioritaria = Fila.objects.filter(sigla='P').first()
    proxima_senha = Senha.objects.filter(fila=fila_prioritaria, status='AGU').order_by('data_emissao').first()

    if not proxima_senha:
        proxima_senha = Senha.objects.filter(status='AGU').order_by('data_emissao').first()

    if proxima_senha:
        proxima_senha.status = 'CHA'
        proxima_senha.data_chamada = timezone.now()
        proxima_senha.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'fila_geral',
            {
                'type': 'fila_update',
                'message': str(proxima_senha)
            }
        )

    return redirect('painel_atendente')


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

@user_passes_test(is_staff)
def finalizar_atendimento(request, senha_id):
    if request.method == 'POST':
        senha_a_finalizar = get_object_or_404(Senha, pk=senha_id)
        if senha_a_finalizar.data_chamada:
            Historico.objects.create(
                senha=senha_a_finalizar,
                atendente=request.user,
                data_inicio_atendimento=senha_a_finalizar.data_chamada
            )
        senha_a_finalizar.status = 'FIN'
        senha_a_finalizar.save()

    return redirect('painel_atendente')