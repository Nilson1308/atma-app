from django.db import models
from apps.users.models import Profissional, Paciente
from apps.agenda.models import Agendamento

class EntradaProntuario(models.Model):
    """
    Modelo para cada registro no prontuário de um paciente.
    """
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='prontuarios'
    )
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.SET_NULL, # Se o profissional for excluído, mantém o registro
        null=True,
        related_name='entradas_prontuario'
    )
    agendamento_associado = models.OneToOneField(
        Agendamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Opcional
        related_name='prontuario'
    )
    data_hora = models.DateTimeField(auto_now_add=True)
    evolucao = models.TextField(verbose_name="Evolução do Paciente")

    class Meta:
        ordering = ['-data_hora'] # Ordena as entradas da mais recente para a mais antiga

    def __str__(self):
        return f"Prontuário de {self.paciente.nome_completo} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

