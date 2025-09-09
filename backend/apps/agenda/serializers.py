from rest_framework import serializers
from .models import Agendamento

class AgendamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Agendamento.
    Converte os dados do Agendamento para JSON.
    """
    # Para facilitar a exibição no frontend, incluímos os nomes em vez de apenas os IDs.
    paciente_nome = serializers.CharField(source='paciente.nome_completo', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome_completo', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome_servico', read_only=True, allow_null=True)

    class Meta:
        model = Agendamento
        # Expomos todos os campos do modelo, pois serão úteis no frontend.
        fields = '__all__'
        # Adicionamos os campos extras que criamos acima à lista de campos a serem lidos.
        read_only_fields = ['paciente_nome', 'profissional_nome', 'servico_nome', 'profissional']

