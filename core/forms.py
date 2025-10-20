from django import forms
from django.contrib.auth.models import User
from .models import Paciente


class UserForm(forms.ModelForm):
    
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ('cpf',)

# FORMULÁRIO: Para o Atendente registrar as observações
class ObservacaoAtendimentoForm(forms.Form):
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False, 
        label="Observações do Atendimento (Opcional)"
    )