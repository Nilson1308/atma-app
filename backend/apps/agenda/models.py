from django.db import models
# Removido: from apps.users.models import Paciente, Profissional
# Removido: from apps.financas.models import Servico

class Agendamento(models.Model):
    """
    Modelo para armazenar os agendamentos dos profissionais.
    """
    # Opções para o campo de status
    STATUS_CHOICES = [
        ('Agendado', 'Agendado'),
        ('Confirmado', 'Confirmado'),
        ('Cancelado', 'Cancelado'),
        ('Realizado', 'Realizado'),
        ('Não Compareceu', 'Não Compareceu'),
    ]

    # Relacionamentos usando string reference para evitar importação circular
    paciente = models.ForeignKey(
        'users.Paciente', # <-- Alterado
        on_delete=models.CASCADE,
        related_name='agendamentos'
    )
    profissional = models.ForeignKey(
        'users.Profissional', # <-- Alterado
        on_delete=models.CASCADE,
        related_name='agendamentos'
    )
    servico = models.ForeignKey(
        'financas.Servico', # <-- Alterado
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos'
    )

    # Informações do Agendamento
    titulo = models.CharField(max_length=200)
    data_hora_inicio = models.DateTimeField()
    data_hora_fim = models.DateTimeField()
    notas_agendamento = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Agendado')

    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-data_hora_inicio']

    def __str__(self):
        # Acessamos o paciente através do self para evitar a importação
        return f"{self.titulo} - {self.paciente.nome_completo} ({self.data_hora_inicio.strftime('%d/%m/%Y %H:%M')})"

