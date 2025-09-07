from rest_framework import viewsets, permissions
from .models import Agendamento
from .serializers import AgendamentoSerializer
from apps.financas.models import Transacao # Importa o modelo de Transação

class AgendamentoViewSet(viewsets.ModelViewSet):
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Retorna apenas os agendamentos do profissional logado
        return Agendamento.objects.filter(profissional=self.request.user)

    def perform_create(self, serializer):
        # Associa o profissional logado automaticamente ao criar um novo agendamento
        serializer.save(profissional=self.request.user)

    def perform_update(self, serializer):
        # Pega o estado do objeto *antes* de salvar
        old_status = serializer.instance.status
        
        # Salva a alteração
        instance = serializer.save()

        # Pega o novo status
        new_status = instance.status

        # Lógica para criar a transação automaticamente
        if new_status == 'Realizado' and old_status != 'Realizado':
            # Verifica se o agendamento tem um serviço e se já não existe uma transação para ele
            if instance.servico and not Transacao.objects.filter(agendamento=instance).exists():
                Transacao.objects.create(
                    profissional=instance.profissional,
                    paciente=instance.paciente,
                    agendamento=instance,
                    servico_prestado=instance.servico,
                    valor_cobrado=instance.servico.valor_padrao,
                    status='pendente'
                )
        
        return instance


class PacienteAgendamentoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtra os agendamentos pelo paciente_pk da URL e pelo profissional logado
        paciente_pk = self.kwargs.get('paciente_pk')
        return Agendamento.objects.filter(
            paciente__pk=paciente_pk,
            profissional=self.request.user
        )
