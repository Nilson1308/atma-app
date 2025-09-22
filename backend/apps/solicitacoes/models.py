from django.db import models
from apps.users.models import Paciente, Profissional, Conta

class Solicitacao(models.Model):
    TIPO_CHOICES = [
        ('RECEITA', 'Receita'),
        ('ATESTADO', 'Atestado/Declaração'),
        ('RECIBO', 'Recibo para Reembolso'),
        ('OUTRO', 'Outro'),
    ]
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONCLUIDO', 'Concluído'),
    ]

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='solicitacoes')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='solicitacoes')
    profissional_atribuido = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitacoes')
    
    tipo_solicitacao = models.CharField(max_length=50, choices=TIPO_CHOICES)
    detalhes = models.TextField(blank=True, null=True, help_text="Detalhes adicionais fornecidos pelo paciente ou IA.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data_solicitacao']
        verbose_name = "Solicitação de Paciente"
        verbose_name_plural = "Solicitações de Pacientes"

    def __str__(self):
        return f"{self.get_tipo_solicitacao_display()} - {self.paciente.nome_completo}"