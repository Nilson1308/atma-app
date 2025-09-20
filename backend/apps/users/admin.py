from django.contrib import admin
from .models import Profissional, Paciente, Conta, Plano, Assinatura, CategoriaFAQ, ItemFAQ

@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome_conta', 'proprietario', 'data_criacao')
    search_fields = ('nome_conta', 'proprietario__nome_completo')

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco_mensal', 'limite_usuarios', 'limite_mensagens_ia')

@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ('conta', 'plano', 'ativa', 'data_inicio')
    list_filter = ('plano', 'ativa')

@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome_completo', 'conta', 'is_staff')
    search_fields = ('email', 'nome_completo', 'conta__nome_conta')
    list_filter = ('conta', 'is_staff', 'is_active')

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'conta', 'contato_telefone', 'cadastrado_por')
    search_fields = ('nome_completo', 'cpf', 'email', 'conta__nome_conta')
    list_filter = ('conta',)

@admin.register(CategoriaFAQ)
class CategoriaFAQAdmin(admin.ModelAdmin):
    list_display = ('nome', 'conta')
    list_filter = ('conta',)

@admin.register(ItemFAQ)
class ItemFAQAdmin(admin.ModelAdmin):
    list_display = ('intencao_chave', 'categoria', 'conta')
    list_filter = ('conta', 'categoria')
    search_fields = ('intencao_chave', 'perguntas_exemplo', 'resposta')