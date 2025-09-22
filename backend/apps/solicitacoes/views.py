from rest_framework import viewsets, permissions
from django.utils import timezone
from .models import Solicitacao
from .serializers import SolicitacaoSerializer

class SolicitacaoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar as solicitações dos pacientes da conta.
    """
    serializer_class = SolicitacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Solicitacao.objects.filter(conta=self.request.user.conta)

    def perform_update(self, serializer):
        # Se o status for alterado para 'CONCLUIDO', registra a data
        if serializer.validated_data.get('status') == 'CONCLUIDO' and serializer.instance.status != 'CONCLUIDO':
            serializer.save(data_conclusao=timezone.now())
        else:
            serializer.save()