from rest_framework import serializers
from .models import Profissional, Paciente, Conta, Plano, Assinatura, CategoriaFAQ, ItemFAQ, PerfilClinica

class PlanoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plano
        fields = ['nome']

class AssinaturaSerializer(serializers.ModelSerializer):
    plano = PlanoSerializer(read_only=True)
    class Meta:
        model = Assinatura
        fields = ['plano', 'ativa']

class PerfilClinicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilClinica
        fields = ['bio', 'endereco_completo', 'site_url', 'instagram_handle', 'logotipo']

class ContaSerializer(serializers.ModelSerializer):
    assinatura = AssinaturaSerializer(read_only=True)
    perfil = PerfilClinicaSerializer(read_only=True)
    class Meta:
        model = Conta
        fields = ['id', 'nome_conta', 'assinatura', 'perfil']

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

class ItemFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemFAQ
        fields = ['id', 'intencao_chave', 'perguntas_exemplo', 'resposta', 'categoria']
        read_only_fields = ['conta']

class CategoriaFAQSerializer(serializers.ModelSerializer):
    itens = ItemFAQSerializer(many=True, read_only=True)

    class Meta:
        model = CategoriaFAQ
        fields = ['id', 'nome', 'itens']
        read_only_fields = ['conta']