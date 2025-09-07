from rest_framework_nested import routers
from .views import DocumentoViewSet

router = routers.SimpleRouter()
router.register(r'documentos', DocumentoViewSet, basename='paciente-documentos')

urlpatterns = router.urls
