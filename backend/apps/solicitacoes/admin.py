from django.contrib import admin
from .models import Solicitacao

@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'conta', 'tipo_solicitacao', 'status', 'data_solicitacao')
    list_filter = ('status', 'tipo_solicitacao', 'conta')
    search_fields = ('paciente__nome_completo',)