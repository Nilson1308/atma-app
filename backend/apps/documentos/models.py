from django.db import models
from apps.users.models import Paciente, Profissional

def user_directory_path(instance, filename):
    # O arquivo será salvo em MEDIA_ROOT/paciente_<id>/<filename>
    return f'paciente_{instance.paciente.id}/{filename}'

class Documento(models.Model):
    """
    Modelo para armazenar documentos (exames, laudos) de um paciente.
    """
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_enviados'
    )
    descricao = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to=user_directory_path)
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_upload']

    def __str__(self):
        return f"Documento '{self.descricao}' de {self.paciente.nome_completo}"

