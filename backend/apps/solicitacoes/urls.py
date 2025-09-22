from rest_framework.routers import DefaultRouter
from .views import SolicitacaoViewSet

router = DefaultRouter()
router.register(r'solicitacoes', SolicitacaoViewSet, basename='solicitacao')

urlpatterns = router.urls