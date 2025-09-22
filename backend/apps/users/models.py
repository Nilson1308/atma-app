from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager

class Conta(models.Model):
    """ Representa a conta de uma clínica ou profissional, que é a entidade que assina um plano. """
    nome_conta = models.CharField(max_length=255, help_text="Nome da clínica ou do profissional")
    proprietario = models.OneToOneField(
        'Profissional', 
        on_delete=models.CASCADE, 
        related_name='conta_proprietario'
    )
    whatsapp_number = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        unique=True, 
        help_text="Número de WhatsApp da clínica (formato: 55119...)"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_conta

def logo_directory_path(instance, filename):
    # O arquivo será salvo em MEDIA_ROOT/conta_<id>/logo/<filename>
    return f'conta_{instance.conta.id}/logo/{filename}'

class PerfilClinica(models.Model):
    """
    Armazena os dados de perfil público da clínica/conta.
    """
    conta = models.OneToOneField(Conta, on_delete=models.CASCADE, related_name='perfil')
    bio = models.TextField(blank=True, null=True, help_text="Uma breve descrição sobre a clínica ou profissional.")
    endereco_completo = models.CharField(max_length=255, blank=True, null=True)
    site_url = models.URLField(blank=True, null=True)
    instagram_handle = models.CharField(max_length=100, blank=True, null=True, help_text="Apenas o nome de usuário, sem o '@'.")
    logotipo = models.ImageField(upload_to=logo_directory_path, null=True, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.conta.nome_conta}"

class Profissional(AbstractUser):
    """
    Modelo customizado de usuário para os profissionais de saúde.
    """
    FUNCAO_CHOICES = [
        ('proprietario', 'Proprietário'),
        ('profissional', 'Profissional'),
    ]
    funcao = models.CharField(
        max_length=20, 
        choices=FUNCAO_CHOICES, 
        default='profissional', 
        help_text="Define o nível de permissão do usuário na conta."
    )
    username = None
    email = models.EmailField('endereço de email', unique=True)
    nome_completo = models.CharField(max_length=255)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    registro_profissional = models.CharField('registro profissional (CRP, CREFITO, etc.)', max_length=50, blank=True, null=True)
    contato_telefone = models.CharField('telefone', max_length=20, blank=True, null=True)
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='profissionais', null=True, blank=True)
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
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='pacientes')
    cadastrado_por = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacientes_cadastrados')
    data_cadastro = models.DateTimeField(auto_now_add=True)
    conversation_state = models.CharField(max_length=50, null=True, blank=True, help_text="Controla o estado da conversa com a IA")

    def __str__(self):
        return self.nome_completo

class Plano(models.Model):
    NOME_CHOICES = [
        ('BASICO', 'Básico'),
        ('INTERMEDIARIO', 'Intermediário'),
        ('PREMIUM', 'Premium'),
    ]
    nome = models.CharField(max_length=50, choices=NOME_CHOICES, unique=True)
    limite_usuarios = models.PositiveIntegerField(default=1)
    limite_mensagens_ia = models.PositiveIntegerField(default=0)
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.get_nome_display()

class Assinatura(models.Model):
    conta = models.OneToOneField(Conta, on_delete=models.CASCADE, related_name='assinatura')
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT)
    ativa = models.BooleanField(default=True)
    data_inicio = models.DateField(auto_now_add=True)
    data_fim = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.conta.proprietario.nome_completo} - Plano {self.plano.get_nome_display()}"

class CategoriaFAQ(models.Model):
    """ Ex: Informações Gerais, Convênios, Agendamento """
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='categorias_faq')
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Categoria do FAQ"
        verbose_name_plural = "Categorias do FAQ"

    def __str__(self):
        return self.nome

class ItemFAQ(models.Model):
    """ Uma pergunta e resposta específica dentro de uma categoria. """
    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='itens_faq')
    categoria = models.ForeignKey(CategoriaFAQ, on_delete=models.CASCADE, related_name='itens')
    
    intencao_chave = models.CharField(
        max_length=100,
        help_text="Uma palavra-chave única para a IA identificar a intenção. Ex: 'verificar_convenios' (use apenas letras minúsculas e underscore)"
    )
    perguntas_exemplo = models.TextField(help_text="Exemplos de perguntas que os pacientes fazem, separadas por ponto e vírgula (;).")
    
    resposta = models.TextField(help_text="A resposta exata que a secretária IA deve dar.")

    class Meta:
        verbose_name = "Item do FAQ"
        verbose_name_plural = "Itens do FAQ"
        # Garante que a mesma intenção não seja cadastrada duas vezes para a mesma conta
        unique_together = ('conta', 'intencao_chave')

    def __str__(self):
        return self.intencao_chave