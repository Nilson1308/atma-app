from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import EntradaProntuario, Paciente
from .serializers import EntradaProntuarioSerializer

class EntradaProntuarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint para as entradas de prontuário de um paciente específico.
    """
    serializer_class = EntradaProntuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna as entradas de prontuário apenas para o paciente especificado na URL
        e garante que o paciente pertença ao profissional logado.
        """
        paciente_pk = self.kwargs.get('paciente_pk')
        try:
            paciente = Paciente.objects.get(pk=paciente_pk, conta=self.request.user.conta)
            return EntradaProntuario.objects.filter(paciente=paciente)
        except Paciente.DoesNotExist:
            return EntradaProntuario.objects.none()

    def perform_create(self, serializer):
        """
        Cria uma nova entrada de prontuário, associando-a ao paciente da URL
        e ao profissional logado.
        """
        paciente_pk = self.kwargs.get('paciente_pk')
        try:
            paciente = Paciente.objects.get(pk=paciente_pk, conta=self.request.user.conta)
            serializer.save(profissional=self.request.user, paciente=paciente)
        except Paciente.DoesNotExist:
            raise permissions.PermissionDenied("Você não tem permissão para adicionar um prontuário para este paciente.")

