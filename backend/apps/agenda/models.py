from django.db import models
from apps.users.models import Profissional, Paciente
from apps.financas.models import Servico
import uuid

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
        ('Reagendar', 'Reagendar'),
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
    lembrete_enviado = models.BooleanField(default=False)
    token_confirmacao = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    follow_up_enviado = models.BooleanField(default=False)

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

class HorarioTrabalho(models.Model):
    """
    Define o horário de trabalho padrão do profissional para cada dia da semana.
    """
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='horarios_trabalho')
    dia_da_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        # Garante que um profissional só tenha um horário por dia da semana
        unique_together = ('profissional', 'dia_da_semana')
        ordering = ['dia_da_semana']

    def __str__(self):
        return f"{self.get_dia_da_semana_display()}: {self.hora_inicio.strftime('%H:%M')} - {self.hora_fim.strftime('%H:%M')}"


class ExcecaoHorario(models.Model):
    """
    Define exceções à regra, como feriados, férias ou dias com horários especiais.
    """
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='excecoes_horario')
    data = models.DateField()
    dia_inteiro = models.BooleanField(default=True, help_text="Marque se for um dia inteiro de folga.")
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fim = models.TimeField(null=True, blank=True)
    descricao = models.CharField(max_length=255, help_text="Ex: Feriado, Férias, Congresso")

    def __str__(self):
        return f"Exceção em {self.data.strftime('%d/%m/%Y')} - {self.descricao}"

class LogMensagemIA(models.Model):
    assinatura = models.ForeignKey('users.Assinatura', on_delete=models.CASCADE, related_name='logs_mensagens')
    data_envio = models.DateTimeField(auto_now_add=True)
    sid_twilio = models.CharField(max_length=255, unique=True) # ID da mensagem retornado pela Twilio