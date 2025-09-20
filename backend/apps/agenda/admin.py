from django.contrib import admin
from .models import Agendamento, HorarioTrabalho, ExcecaoHorario, LogMensagemIA

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    """
    Configuração da interface de administração para o modelo Agendamento.
    """
    llist_display = ('titulo', 'paciente', 'profissional', 'get_conta', 'data_hora_inicio', 'status')
    list_filter = ('status', 'profissional__conta', 'data_hora_inicio') # Filtro por conta
    search_fields = ('titulo', 'paciente__nome_completo', 'profissional__nome_completo', 'profissional__conta__nome_conta')
    date_hierarchy = 'data_hora_inicio'
    ordering = ('-data_hora_inicio',)

    # Função para buscar o nome da conta através do profissional
    @admin.display(description='Conta/Clínica')
    def get_conta(self, obj):
        if obj.profissional:
            return obj.profissional.conta
        return "N/A"

@admin.register(HorarioTrabalho)
class HorarioTrabalhoAdmin(admin.ModelAdmin):
    list_display = ('profissional', 'get_conta', 'get_dia_da_semana_display', 'hora_inicio', 'hora_fim', 'ativo')
    list_filter = ('profissional__conta', 'dia_da_semana', 'ativo')

    @admin.display(description='Conta/Clínica')
    def get_conta(self, obj):
        return obj.profissional.conta

@admin.register(ExcecaoHorario)
class ExcecaoHorarioAdmin(admin.ModelAdmin):
    list_display = ('profissional', 'get_conta', 'data', 'descricao', 'dia_inteiro')
    list_filter = ('profissional__conta', 'data')

    @admin.display(description='Conta/Clínica')
    def get_conta(self, obj):
        return obj.profissional.conta

@admin.register(LogMensagemIA)
class LogMensagemIAAdmin(admin.ModelAdmin):
    list_display = ('get_profissional', 'get_conta', 'data_envio')
    readonly_fields = ('assinatura', 'data_envio', 'sid_twilio')

    @admin.display(description='Profissional')
    def get_profissional(self, obj):
        return obj.assinatura.conta.proprietario

    @admin.display(description='Conta/Clínica')
    def get_conta(self, obj):
        return obj.assinatura.conta