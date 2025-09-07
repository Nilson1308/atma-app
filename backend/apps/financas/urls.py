from rest_framework.routers import DefaultRouter
from .views import ServicoViewSet, TransacaoViewSet

router = DefaultRouter()
router.register(r'servicos', ServicoViewSet, basename='servico')
router.register(r'transacoes', TransacaoViewSet, basename='transacao')

urlpatterns = router.urls
