from rest_framework import serializers
from .models import Solicitacao
from apps.users.serializers import PacienteSerializerSimple

class SolicitacaoSerializer(serializers.ModelSerializer):
    paciente = PacienteSerializerSimple(read_only=True)
    
    class Meta:
        model = Solicitacao
        fields = '__all__'
        read_only_fields = ['conta', 'paciente', 'data_solicitacao', 'data_conclusao']