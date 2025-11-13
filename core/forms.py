# core/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Paciente, PerfilAtendente 

# Formulários de autenticação e cadastro
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="CPF", max_length=11, widget=forms.TextInput(attrs={'class': 'form-control'}))

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['cpf']
        widgets = {
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 11}),
        }
        
class ObservacaoAtendimentoForm(forms.Form):
    observacoes = forms.CharField(
        label='Observações do Atendimento',
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False
    )
    
# --- NOVOS FORMULÁRIOS DE PERFIL (RF05, RF06) ---

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
        }
        widgets = {
             'first_name': forms.TextInput(attrs={'class': 'form-control'}),
             'last_name': forms.TextInput(attrs={'class': 'form-control'}),
             'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
class PerfilAtendenteForm(forms.ModelForm):
    class Meta:
        model = PerfilAtendente
        fields = ['filas_atendidas']
        labels = {
            'filas_atendidas': 'Filas que você atende',
        }
        widgets = {
            # Usa CheckboxSelectMultiple para facilitar a seleção de várias filas
            'filas_atendidas': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
        }