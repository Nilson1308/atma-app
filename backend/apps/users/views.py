from rest_framework import viewsets, permissions, filters
from .models import Profissional, Paciente
from .serializers import ProfissionalSerializer, PacienteSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from apps.agenda.models import Agendamento
from apps.agenda.serializers import AgendamentoSerializer
from apps.financas.models import Transacao
from apps.users.serializers import PacienteSerializerSimple

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

class DashboardDataView(APIView):
    """
    View para agregar e fornecer todos os dados necessários para o dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profissional = request.user
        hoje = timezone.localdate()
        proximos_7_dias = hoje + timedelta(days=7)

        # 1. Próximos Agendamentos
        agendamentos_hoje = Agendamento.objects.filter(
            profissional=profissional,
            data_hora_inicio__date=hoje,
            status__in=['Agendado', 'Confirmado']
        ).order_by('data_hora_inicio')

        agendamentos_futuros = Agendamento.objects.filter(
            profissional=profissional,
            data_hora_inicio__date__gt=hoje,
            data_hora_inicio__date__lte=proximos_7_dias,
            status__in=['Agendado', 'Confirmado']
        ).order_by('data_hora_inicio')[:5] # Limita a 5 para não poluir o dashboard

        # 2. Total de Pagamentos Pendentes
        total_pendente_query = Transacao.objects.filter(
            profissional=profissional,
            status='pendente'
        ).aggregate(total=Sum('valor_cobrado'))
        total_pendente = total_pendente_query['total'] or 0.00

        # 3. Pacientes Recentes
        pacientes_recentes = Paciente.objects.filter(
            cadastrado_por=profissional
        ).order_by('-data_cadastro')[:5]

        # 4. Aniversariantes do Mês
        aniversariantes_mes = Paciente.objects.filter(
            cadastrado_por=profissional,
            data_nascimento__isnull=False,
            data_nascimento__month=hoje.month
        ).order_by('data_nascimento__day')

        # Serializando os dados para a resposta
        data = {
            'agendamentos_hoje': AgendamentoSerializer(agendamentos_hoje, many=True).data,
            'agendamentos_futuros': AgendamentoSerializer(agendamentos_futuros, many=True).data,
            'total_pendente': total_pendente,
            'pacientes_recentes': PacienteSerializerSimple(pacientes_recentes, many=True).data,
            'aniversariantes_mes': PacienteSerializerSimple(aniversariantes_mes, many=True).data,
        }

        return Response(data)