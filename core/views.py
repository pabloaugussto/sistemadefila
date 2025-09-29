from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from .models import Fila, Senha

def selecionar_fila(request):
    filas = Fila.objects.all()
    contexto = {'filas': filas}
    return render(request, 'core/selecionar_fila.html', contexto)

def emitir_senha(request):
    if request.method == 'POST':
        fila_id = request.POST.get('fila_id')
        fila_selecionada = get_object_or_404(Fila, pk=fila_id)

        # Lógica para pegar o último número da senha e adicionar 1
        ultimo_numero = Senha.objects.filter(fila=fila_selecionada).aggregate(Max('numero_senha'))['numero_senha__max']
        proximo_numero = (ultimo_numero or 0) + 1

        # Cria a nova senha
        nova_senha = Senha.objects.create(
            fila=fila_selecionada,
            numero_senha=proximo_numero
        )
        
        # Redireciona para a futura página de acompanhamento
        # Por enquanto, vamos redirecionar de volta para a seleção
        return redirect('selecionar_fila') 

    # Se não for POST, redireciona para a página de seleção
    return redirect('selecionar_fila') 