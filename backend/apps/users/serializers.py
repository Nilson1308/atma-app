from rest_framework import serializers
from .models import Profissional, Paciente, Conta, Plano, Assinatura

class PlanoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plano
        fields = ['nome']

class AssinaturaSerializer(serializers.ModelSerializer):
    plano = PlanoSerializer(read_only=True)
    class Meta:
        model = Assinatura
        fields = ['plano', 'ativa']

class ContaSerializer(serializers.ModelSerializer):
    assinatura = AssinaturaSerializer(read_only=True)
    class Meta:
        model = Conta
        fields = ['id', 'nome_conta', 'assinatura']

class ProfissionalSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Profissional.
    """
    conta = ContaSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Profissional
        fields = ['id', 'email', 'nome_completo', 'especialidade', 'registro_profissional', 'contato_telefone', 'conta', 'password', 'funcao'] # Adicionei 'funcao' aqui também

    def create(self, validated_data):
        user = Profissional.objects.create_user(**validated_data)
        return user


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Paciente.
    """
    cadastrado_por_nome = serializers.CharField(source='cadastrado_por.nome_completo', read_only=True)
    conta = ContaSerializer(read_only=True)

    class Meta:
        model = Paciente
        fields = '__all__'
        read_only_fields = ['cadastrado_por', 'conta']

class PacienteSerializerSimple(serializers.ModelSerializer):
    """
    Um serializer simplificado para mostrar informações básicas do paciente.
    """
    class Meta:
        model = Paciente
        fields = ['id', 'nome_completo']