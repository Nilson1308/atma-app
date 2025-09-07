from rest_framework import serializers
from .models import EntradaProntuario

class EntradaProntuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo EntradaProntuario.
    """
    # Para facilitar, incluímos o nome do profissional que fez a entrada.
    profissional_nome = serializers.CharField(source='profissional.nome_completo', read_only=True)

    class Meta:
        model = EntradaProntuario
        fields = '__all__'
        # O profissional é definido automaticamente pela view.
        read_only_fields = ['profissional', 'profissional_nome', 'paciente']

