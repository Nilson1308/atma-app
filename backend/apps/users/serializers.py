from rest_framework import serializers
from .models import Profissional, Paciente

class ProfissionalSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Profissional.
    Converte os dados do Profissional para JSON.
    """
    class Meta:
        model = Profissional
        # Define os campos que serão expostos na API.
        # É mais seguro não expor a senha (password).
        fields = ['id', 'email', 'nome_completo', 'especialidade', 'registro_profissional', 'contato_telefone']


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Paciente.
    Converte os dados do Paciente para JSON.
    """
    # Incluímos o nome do profissional que cadastrou para facilitar no frontend
    cadastrado_por_nome = serializers.CharField(source='cadastrado_por.nome_completo', read_only=True)

    class Meta:
        model = Paciente
        # Expõe todos os campos do modelo Paciente.
        fields = '__all__'
        # Adicionamos o campo extra que criamos acima.
        extra_fields = ['cadastrado_por_nome']

class PacienteSerializerSimple(serializers.ModelSerializer):
    """
    Um serializer simplificado para mostrar informações básicas do paciente.
    """
    class Meta:
        model = Paciente
        fields = ['id', 'nome_completo']