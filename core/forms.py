from django import forms
from django.contrib.auth.models import User
from .models import Paciente
from django.contrib.auth.forms import AuthenticationForm


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

# FORMULÁRIO: Para o Atendente registrar as observações (Mantido do seu HEAD)
class ObservacaoAtendimentoForm(forms.Form):
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False, 
        label="Observações do Atendimento (Opcional)"
    )

# FORMULÁRIO: Customização do formulário de login (Adicionado do commit remoto)
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'CPF'