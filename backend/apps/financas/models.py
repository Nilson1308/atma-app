from django.db import models
from django.utils import timezone
# Importa a Conta e o Profissional do app users
from apps.users.models import Profissional, Paciente, Conta

class Servico(models.Model):
    # --- CAMPO ALTERADO ---
    # O serviço agora pertence a uma Conta/Clínica
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='servicos')
    nome_servico = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    duracao_padrao = models.IntegerField(help_text="Duração em minutos")
    valor_padrao = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome_servico

class Transacao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('cancelado', 'Cancelado'),
    ]
    METODO_CHOICES = [
        ('Pix', 'Pix'),
        ('Dinheiro', 'Dinheiro'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('Transferência', 'Transferência'),
    ]

    # A transação continua ligada ao profissional que a realizou
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='transacoes')
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='transacoes')
    agendamento = models.ForeignKey('agenda.Agendamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='transacao')
    servico_prestado = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='transacoes')
    data_transacao = models.DateField(default=timezone.localdate, help_text="Data de competência da transação")
    valor_cobrado = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    metodo_pagamento = models.CharField(max_length=50, choices=METODO_CHOICES, blank=True, null=True)
    data_pagamento = models.DateField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    lembrete_pagamento_enviado = models.BooleanField(default=False)

    def __str__(self):
        return f"Transação de {self.valor_cobrado} para {self.paciente.nome_completo}"