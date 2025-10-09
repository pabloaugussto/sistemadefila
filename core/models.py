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
        ('FIN', 'Finalizada'),
    ]

    fila = models.ForeignKey(Fila, on_delete=models.CASCADE)
    numero_senha = models.PositiveIntegerField()
    data_emissao = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='AGU') 
    paciente = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    data_chamada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.fila.sigla}{self.numero_senha:03d}"
    
    class Meta:
        unique_together = ('fila', 'numero_senha')

class Paciente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=11, unique=True, verbose_name="CPF")

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
class Historico(models.Model):
    senha = models.OneToOneField(Senha, on_delete=models.CASCADE)
    atendente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='atendimentos_realizados')
    data_inicio_atendimento = models.DateTimeField()
    data_fim_atendimento = models.DateTimeField(auto_now_add=True)

    def tempo_total_atendimento(self):
        return self.data_fim_atendimento - self.data_inicio_atendimento

    def __str__(self):
        return f"Atendimento da Senha {self.senha}"
      