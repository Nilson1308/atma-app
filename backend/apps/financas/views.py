from rest_framework import viewsets, permissions, filters
from .models import Servico, Transacao
from .serializers import ServicoSerializer, TransacaoSerializer

class ServicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o profissional gerenciar seu catálogo de serviços.
    """
    serializer_class = ServicoSerializer
    permission_classes = [permissions.IsAuthenticated]

    # --- CORREÇÃO ADICIONADA ---
    # Habilita a funcionalidade de busca na API para o campo 'nome_servico'
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome_servico']

    def get_queryset(self):
        """
        Retorna apenas os serviços que pertencem ao profissional logado.
        """
        return Servico.objects.filter(profissional=self.request.user)

    def perform_create(self, serializer):
        """
        Associa o profissional logado automaticamente ao criar um novo serviço.
        """
        serializer.save(profissional=self.request.user)


class TransacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o profissional gerenciar suas transações financeiras.
    """
    serializer_class = TransacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna apenas as transações que pertencem ao profissional logado.
        """
        # Filtra as transações baseadas no profissional do agendamento associado
        return Transacao.objects.filter(agendamento__profissional=self.request.user)
