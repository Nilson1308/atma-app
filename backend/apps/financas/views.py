from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Servico, Transacao
from .serializers import ServicoSerializer, TransacaoSerializer

class ServicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o profissional gerenciar seu catálogo de serviços.
    """
    serializer_class = ServicoSerializer
    permission_classes = [permissions.IsAuthenticated]
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
        return Transacao.objects.filter(profissional=self.request.user)

    @action(detail=False, methods=['post'], url_path='marcar-como-pago-em-lote')
    def marcar_como_pago_em_lote(self, request):
        """
        Ação para marcar múltiplas transações como pagas de uma só vez.
        """
        transacao_ids = request.data.get('transacao_ids', [])
        data_pagamento = request.data.get('data_pagamento')
        metodo_pagamento = request.data.get('metodo_pagamento')

        if not all([transacao_ids, data_pagamento, metodo_pagamento]):
            return Response(
                {"error": "Os campos 'transacao_ids', 'data_pagamento' e 'metodo_pagamento' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        transacoes_para_pagar = Transacao.objects.filter(
            id__in=transacao_ids,
            profissional=request.user,
            status='pendente'
        )

        if not transacoes_para_pagar.exists():
            return Response(
                {"error": "Nenhuma transação pendente válida foi encontrada para os IDs fornecidos."},
                status=status.HTTP_404_NOT_FOUND
            )

        atualizadas = transacoes_para_pagar.update(
            status='pago',
            data_pagamento=data_pagamento,
            metodo_pagamento=metodo_pagamento
        )

        return Response(
            {"message": f"{atualizadas} transação(ões) marcada(s) como paga(s) com sucesso."},
            status=status.HTTP_200_OK
        )

class PacienteTransacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar as transações de um paciente específico.
    """
    serializer_class = TransacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna as transações para o paciente especificado na URL,
        garantindo que o paciente pertença ao profissional logado.
        """
        paciente_pk = self.kwargs.get('paciente_pk')
        return Transacao.objects.filter(
            paciente__pk=paciente_pk,
            profissional=self.request.user
        ).order_by('-data_transacao')