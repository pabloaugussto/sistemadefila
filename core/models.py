# core/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Fila(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=3, unique=True, help_text="Ex: 'N' para Normal, 'P' para Prioritário")

    def __str__(self):
        return self.nome

class Senha(models.Model):
    STATUS_CHOICES = [
        ('AGU', 'Aguardando'),
        ('CHA', 'Chamada'),
        ('ATE', 'Em Atendimento'),
        ('FIN', 'Finalizada'),
    ]

    fila = models.ForeignKey(Fila, on_delete=models.CASCADE)
    numero_senha = models.PositiveIntegerField()
    data_emissao = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='AGU')
    
    paciente = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Campos do Atendente
    atendente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='senhas_atendidas', verbose_name='Atendente')
    
    hora_chamada = models.DateTimeField(null=True, blank=True)
    hora_inicio_atendimento = models.DateTimeField(null=True, blank=True)
    hora_fim_atendimento = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    

    def __str__(self):
        return f"{self.fila.sigla}{self.numero_senha:03d}"
    
    class Meta:
        unique_together = ('fila', 'numero_senha')

class Paciente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=11, unique=True, verbose_name="CPF")

    def __str__(self):
        return self.user.get_full_name() or self.user.username