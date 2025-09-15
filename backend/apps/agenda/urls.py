from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgendamentoViewSet, ConfirmarAgendamentoView, HorarioTrabalhoViewSet, ExcecaoHorarioViewSet

# Cria um roteador para a app de agenda.
router = DefaultRouter()
# Registra a ViewSet de Agendamento sob o endpoint 'agendamentos'.
router.register(r'agendamentos', AgendamentoViewSet, basename='agendamento')
router.register(r'horarios-trabalho', HorarioTrabalhoViewSet, basename='horario-trabalho')
router.register(r'excecoes-horario', ExcecaoHorarioViewSet, basename='excecao-horario')

# As URLs da API para esta app são agora determinadas automaticamente pelo roteador.
urlpatterns = [
    path('agendamentos/confirmar/<uuid:token>/', ConfirmarAgendamentoView.as_view(), name='confirmar-agendamento'),
    path('', include(router.urls)),
]
