from rest_framework_nested import routers
from .views import PacienteTransacaoViewSet

# Este router será registrado dentro do router de pacientes
router = routers.SimpleRouter()
router.register(r'transacoes', PacienteTransacaoViewSet, basename='paciente-transacoes')

urlpatterns = router.urls