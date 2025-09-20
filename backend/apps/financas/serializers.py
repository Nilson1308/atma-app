from rest_framework import serializers
from .models import Servico, Transacao
from apps.agenda.models import Agendamento
from apps.users.models import Paciente
from apps.users.serializers import PacienteSerializerSimple

class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = '__all__'
        read_only_fields = ['conta']

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
        conta_profissional = profissional.conta
        
        # Valida o serviço
        servico = data.get('servico_prestado')
        if servico and servico.conta != conta_profissional:
            raise serializers.ValidationError({"servico_prestado_id": "Este serviço não pertence à sua clínica/conta."})

        paciente = data.get('paciente')
        if paciente and paciente.conta != conta_profissional:
            raise serializers.ValidationError({"paciente_id": "Este paciente não pertence à sua clínica/conta."})
        
        # Valida o agendamento
        agendamento = data.get('agendamento')
        if agendamento and agendamento.profissional.conta != conta_profissional:
            raise serializers.ValidationError({"agendamento_id": "Este agendamento não pertence à sua clínica/conta."})

        return data

    def create(self, validated_data):
        validated_data['profissional'] = self.context['request'].user
        return super().create(validated_data)

