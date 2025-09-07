from rest_framework import serializers
from .models import Servico, Transacao
from apps.agenda.models import Agendamento
from apps.users.models import Paciente
from apps.users.serializers import PacienteSerializerSimple

class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = '__all__'
        read_only_fields = ['profissional']

class AgendamentoTransacaoSerializer(serializers.ModelSerializer):
    paciente = PacienteSerializerSimple(read_only=True)
    class Meta:
        model = Agendamento
        fields = ['id', 'data_hora_inicio', 'paciente']

class TransacaoSerializer(serializers.ModelSerializer):
    servico_prestado = ServicoSerializer(read_only=True)
    servico_prestado_id = serializers.PrimaryKeyRelatedField(
        queryset=Servico.objects.all(), source='servico_prestado', write_only=True
    )
    agendamento = AgendamentoTransacaoSerializer(read_only=True)
    agendamento_id = serializers.PrimaryKeyRelatedField(
        queryset=Agendamento.objects.all(), source='agendamento', write_only=True, required=False, allow_null=True
    )
    paciente = PacienteSerializerSimple(read_only=True)
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=Paciente.objects.all(), source='paciente', write_only=True
    )

    class Meta:
        model = Transacao
        fields = [
            'id', 'agendamento', 'agendamento_id', 'servico_prestado', 'servico_prestado_id',
            'valor_cobrado', 'status', 'metodo_pagamento', 'data_pagamento', 'notas',
            'data_criacao', 'paciente', 'paciente_id', 'data_transacao'
        ]
        read_only_fields = ['profissional'] # O profissional é sempre o usuário logado

    def validate(self, data):
        profissional = self.context['request'].user
        
        # Valida o serviço
        servico = data.get('servico_prestado')
        if servico and servico.profissional != profissional:
            raise serializers.ValidationError({"servico_prestado_id": "Você só pode usar os seus próprios serviços."})

        paciente = data.get('paciente')
        if paciente:
            if not Paciente.objects.filter(pk=paciente.pk, profissional=profissional).exists():
                raise serializers.ValidationError({"paciente_id": "Você só pode criar transações para os seus próprios pacientes."})
        
        # Valida o agendamento
        agendamento = data.get('agendamento')
        if agendamento and agendamento.profissional != profissional:
            raise serializers.ValidationError({"agendamento_id": "Você só pode usar os seus próprios agendamentos."})

        return data

    def create(self, validated_data):
        # Associa o profissional logado automaticamente
        validated_data['profissional'] = self.context['request'].user
        return super().create(validated_data)

