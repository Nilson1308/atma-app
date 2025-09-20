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
    API endpoint que permite que os profissionais da CONTA sejam visualizados ou editados.
    """
    serializer_class = ProfissionalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Retorna apenas os profissionais que pertencem à mesma conta do usuário logado. """
        if self.request.user.is_authenticated:
            return Profissional.objects.filter(conta=self.request.user.conta)
        return Profissional.objects.none()

    def perform_create(self, serializer):
        """
        Permite que um profissional crie outro na mesma conta.
        (Futuramente, adicionar permissão para apenas o proprietário fazer isso).
        """
        serializer.save(conta=self.request.user.conta)

class PacienteViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite que os pacientes da CONTA sejam visualizados ou editados.
    """
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome_completo', 'cpf']

    def get_queryset(self):
        """ Retorna uma lista de todos os pacientes da conta do profissional logado. """
        return Paciente.objects.filter(conta=self.request.user.conta)

    def perform_create(self, serializer):
        """ Ao criar um novo paciente, associa automaticamente à conta e ao profissional logado. """
        serializer.save(
            conta=self.request.user.conta,
            cadastrado_por=self.request.user
        )

class DashboardDataView(APIView):
    """
    View para agregar e fornecer todos os dados necessários para o dashboard da CONTA.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        conta_atual = request.user.conta
        hoje = timezone.localdate()
        proximos_7_dias = hoje + timedelta(days=7)

        agendamentos_hoje = Agendamento.objects.filter(
            profissional__conta=conta_atual,
            data_hora_inicio__date=hoje,
            status__in=['Agendado', 'Confirmado']
        ).order_by('data_hora_inicio')

        agendamentos_futuros = Agendamento.objects.filter(
            profissional__conta=conta_atual,
            data_hora_inicio__date__gt=hoje,
            data_hora_inicio__date__lte=proximos_7_dias,
            status__in=['Agendado', 'Confirmado']
        ).order_by('data_hora_inicio')[:5]

        total_pendente_query = Transacao.objects.filter(
            profissional__conta=conta_atual,
            status='pendente'
        ).aggregate(total=Sum('valor_cobrado'))
        total_pendente = total_pendente_query['total'] or 0.00

        pacientes_recentes = Paciente.objects.filter(
            conta=conta_atual
        ).order_by('-data_cadastro')[:5]

        aniversariantes_mes = Paciente.objects.filter(
            conta=conta_atual,
            data_nascimento__isnull=False,
            data_nascimento__month=hoje.month
        ).order_by('data_nascimento__day')

        data = {
            'agendamentos_hoje': AgendamentoSerializer(agendamentos_hoje, many=True).data,
            'agendamentos_futuros': AgendamentoSerializer(agendamentos_futuros, many=True).data,
            'total_pendente': total_pendente,
            'pacientes_recentes': PacienteSerializerSimple(pacientes_recentes, many=True).data,
            'aniversariantes_mes': PacienteSerializerSimple(aniversariantes_mes, many=True).data,
        }

        return Response(data)

class ProfissionalLogadoView(APIView):
    """
    Retorna os dados do profissional logado e sua conta.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ProfissionalSerializer(request.user)
        return Response(serializer.data)