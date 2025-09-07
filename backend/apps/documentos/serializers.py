from rest_framework import serializers
from .models import Documento

class DocumentoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Documento.
    """
    profissional_nome = serializers.CharField(source='profissional.nome_completo', read_only=True)
    # Garante que a URL completa do arquivo seja retornada na API
    arquivo_url = serializers.FileField(source='arquivo', read_only=True)

    class Meta:
        model = Documento
        fields = ['id', 'paciente', 'profissional', 'profissional_nome', 'descricao', 'arquivo', 'arquivo_url', 'data_upload']
        # O profissional e o paciente são definidos automaticamente pela view.
        read_only_fields = ['profissional', 'paciente', 'profissional_nome', 'arquivo_url']

