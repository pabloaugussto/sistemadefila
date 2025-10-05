from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from .models import Fila, Senha, Paciente 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import UserForm, PacienteForm


# Adicione o decorator @login_required para proteger esta página
@login_required
def selecionar_fila(request):
    filas = Fila.objects.all()
    contexto = {'filas': filas}
    return render(request, 'core/selecionar_fila.html', contexto)


def emitir_senha(request):
    # Lógica para associar a senha ao paciente logado
    if request.user.is_authenticated:
        if request.method == 'POST':
            fila_id = request.POST.get('fila_id')
            fila_selecionada = get_object_or_404(Fila, pk=fila_id)
            
            ultimo_numero = Senha.objects.filter(fila=fila_selecionada).aggregate(Max('numero_senha'))['numero_senha__max']
            proximo_numero = (ultimo_numero or 0) + 1

            # Modificação: Salvar a senha com a referência ao paciente
            nova_senha = Senha.objects.create(
                fila=fila_selecionada,
                numero_senha=proximo_numero,
                paciente=request.user 
            )
            
            return redirect('acompanhar_senha', senha_id=nova_senha.id)

    return redirect('selecionar_fila')


@login_required
def acompanhar_senha(request, senha_id):
    # O conteúdo desta função continua o mesmo
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


@login_required
def painel_atendente(request):
    # O conteúdo desta função continua o mesmo
    filas = Fila.objects.all()
    senhas_aguardando = {}
    for fila in filas:
        senhas_aguardando[fila.nome] = Senha.objects.filter(fila=fila, status='AGU').order_by('data_emissao')

    contexto = {
        'senhas_aguardando': senhas_aguardando
    }
    return render(request, 'core/painel_atendente.html', contexto)


@login_required
def chamar_senha(request):
    # O conteúdo desta função continua o mesmo
    fila_prioritaria = Fila.objects.filter(sigla='P').first()
    proxima_senha = Senha.objects.filter(fila=fila_prioritaria, status='AGU').order_by('data_emissao').first()

    if not proxima_senha:
        proxima_senha = Senha.objects.filter(status='AGU').order_by('data_emissao').first()

    if proxima_senha:
        proxima_senha.status = 'CHA'
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
            # Cria o objeto User mas não salva no banco ainda
            user = user_form.save(commit=False)
            # Define o username como o CPF (que deve ser único)
            user.username = paciente_form.cleaned_data['cpf']
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            # Agora cria o objeto Paciente, associando-o ao usuário recém-criado
            paciente = paciente_form.save(commit=False)
            paciente.user = user
            paciente.save()

            # Loga o novo usuário no sistema e o redireciona
            login(request, user)
            return redirect('selecionar_fila')
    else:
        # Se não for POST, apenas cria os formulários vazios
        user_form = UserForm()
        paciente_form = PacienteForm()
    
    contexto = {
        'user_form': user_form,
        'paciente_form': paciente_form
    }
    return render(request, 'core/cadastro.html', contexto)