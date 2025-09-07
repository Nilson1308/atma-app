from django.contrib import admin
from .models import Profissional, Paciente

# Registra o modelo Profissional para que ele apareça na interface de administração.
@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome_completo', 'especialidade', 'is_staff')
    search_fields = ('email', 'nome_completo')
    list_filter = ('especialidade', 'is_staff', 'is_active')

# Registra o modelo Paciente.
@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'contato_telefone', 'email', 'cadastrado_por')
    search_fields = ('nome_completo', 'cpf', 'email')
    list_filter = ('cadastrado_por',)

