from django.contrib import admin
from .models import EntradaProntuario

@admin.register(EntradaProntuario)
class EntradaProntuarioAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'get_conta', 'profissional', 'data_hora')
    list_filter = ('profissional__conta', 'data_hora')
    search_fields = ('paciente__nome_completo', 'profissional__nome_completo', 'evolucao', 'paciente__conta__nome_conta')
    date_hierarchy = 'data_hora'
    ordering = ('-data_hora',)

    @admin.display(description='Conta/Clínica')
    def get_conta(self, obj):
        return obj.paciente.conta