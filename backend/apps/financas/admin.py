from django.contrib import admin
from .models import Servico, Transacao

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome_servico', 'valor_padrao', 'duracao_padrao', 'ativo', 'profissional')
    list_filter = ('ativo', 'profissional')
    search_fields = ('nome_servico', 'descricao')
    ordering = ('nome_servico',)

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'servico_prestado', 'data_transacao', 'valor_cobrado', 'status', 'data_pagamento', 'profissional')
    list_filter = ('status', 'metodo_pagamento', 'profissional')
    search_fields = ('paciente__nome_completo', 'servico_prestado__nome_servico')
    ordering = ('-data_criacao',)
