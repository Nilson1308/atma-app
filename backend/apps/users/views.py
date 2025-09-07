from rest_framework import viewsets, permissions, filters
from .models import Profissional, Paciente
from .serializers import ProfissionalSerializer, PacienteSerializer

class ProfissionalViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite que os profissionais sejam visualizados ou editados.
    """
    queryset = Profissional.objects.all().order_by('-date_joined')
    serializer_class = ProfissionalSerializer
    # Apenas usuários autenticados podem acessar esta view.
    permission_classes = [permissions.IsAuthenticated]

class PacienteViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite que os pacientes sejam visualizados ou editados.
    """
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome_completo', 'cpf']

    def get_queryset(self):
        """
        Esta view deve retornar uma lista de todos os pacientes
        cadastrados pelo profissional que está logado.
        """
        # Filtra os pacientes para mostrar apenas os que foram cadastrados pelo usuário atual.
        return Paciente.objects.filter(cadastrado_por=self.request.user)

    def perform_create(self, serializer):
        """
        Ao criar um novo paciente, associa automaticamente ao profissional logado.
        """
        # Salva o novo paciente, definindo o campo 'cadastrado_por' como o usuário atual.
        serializer.save(cadastrado_por=self.request.user)

