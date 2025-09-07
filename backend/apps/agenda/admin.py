from django.contrib import admin
from .models import Agendamento

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para o modelo Agendamento.
    """
    list_display = ('titulo', 'paciente', 'profissional', 'data_hora_inicio', 'status')
    list_filter = ('status', 'profissional', 'data_hora_inicio')
    search_fields = ('titulo', 'paciente__nome_completo', 'profissional__nome_completo')
    date_hierarchy = 'data_hora_inicio'
    ordering = ('-data_hora_inicio',)

