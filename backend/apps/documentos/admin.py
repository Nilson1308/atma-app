from django.contrib import admin
from .models import Documento

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'paciente', 'profissional', 'data_upload')
    list_filter = ('profissional', 'data_upload')
    search_fields = ('descricao', 'paciente__nome_completo')
    ordering = ('-data_upload',)
