from django.contrib import admin
from .models import EntradaProntuario

@admin.register(EntradaProntuario)
class EntradaProntuarioAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'profissional', 'data_hora')
    list_filter = ('profissional', 'data_hora')
    search_fields = ('paciente__nome_completo', 'profissional__nome_completo', 'evolucao')
    date_hierarchy = 'data_hora'
    ordering = ('-data_hora',)

