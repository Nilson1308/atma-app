from rest_framework_nested import routers
from .views import PacienteAgendamentoViewSet

# Este router será registrado dentro do router de pacientes
router = routers.SimpleRouter()
router.register(r'agendamentos', PacienteAgendamentoViewSet, basename='paciente-agendamentos')

urlpatterns = router.urls
