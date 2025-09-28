from django.db import models
from django.utils import timezone

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

    def __str__(self):
        # Formata o número da senha com 3 dígitos, ex: 1 -> 001, 15 -> 015
        return f"{self.fila.sigla}{self.numero_senha:03d}"
    
    class Meta:
        # Garante que o número da senha seja único para cada fila
        unique_together = ('fila', 'numero_senha')