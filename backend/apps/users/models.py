from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager

# Modelo para o Profissional
class Profissional(AbstractUser):
    """
    Modelo customizado de usuário para os profissionais de saúde.
    """
    username = None
    email = models.EmailField('endereço de email', unique=True)
    nome_completo = models.CharField(max_length=255)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    registro_profissional = models.CharField('registro profissional (CRP, CREFITO, etc.)', max_length=50, blank=True, null=True)
    contato_telefone = models.CharField('telefone', max_length=20, blank=True, null=True)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='profissional_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_query_name='profissional',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='profissional_set',
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='profissional',
    )
    # --- FIM DA CORREÇÃO ---

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo']

    def __str__(self):
        return self.nome_completo or self.email


# Modelo para o Paciente
class Paciente(models.Model):
    """
    Modelo para armazenar os dados dos pacientes.
    """
    nome_completo = models.CharField(max_length=255)
    data_nascimento = models.DateField(blank=True, null=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, blank=True, null=True)
    contato_telefone = models.CharField('telefone', max_length=20, blank=True, null=True)
    email = models.EmailField('email', max_length=255, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    dia_cobranca = models.IntegerField(
        'Dia de Cobrança Mensal',
        blank=True,
        null=True,
        help_text='Dia do mês para geração da fatura agrupada (de 1 a 31). Deixe em branco para cobrança imediata.'
    )
    cadastrado_por = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacientes_cadastrados')
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_completo
