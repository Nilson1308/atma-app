from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Documento, Paciente
from .serializers import DocumentoSerializer

class DocumentoViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """
        Retorna os documentos do paciente especificado, se ele pertencer à conta do profissional.
        """
        paciente_pk = self.kwargs.get('paciente_pk')
        try:
            paciente = Paciente.objects.get(pk=paciente_pk, conta=self.request.user.conta)
            return Documento.objects.filter(paciente=paciente)
        except Paciente.DoesNotExist:
            return Documento.objects.none()

    def perform_create(self, serializer):
        """
        Cria um novo documento, associando-o ao paciente da URL e ao profissional logado.
        """
        paciente_pk = self.kwargs.get('paciente_pk')
        try:
            paciente = Paciente.objects.get(pk=paciente_pk, conta=self.request.user.conta)
            serializer.save(profissional=self.request.user, paciente=paciente)
        except Paciente.DoesNotExist:
            raise permissions.PermissionDenied("Você não tem permissão para adicionar um documento para este paciente.")