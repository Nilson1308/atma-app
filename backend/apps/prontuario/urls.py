from rest_framework_nested import routers
from .views import EntradaProntuarioViewSet

# Este router será registrado dentro do router de pacientes
router = routers.SimpleRouter()
router.register(r'prontuario', EntradaProntuarioViewSet, basename='paciente-prontuario')

# O urlpatterns é a lista de rotas geradas pelo router.
# Neste caso, ele será incluído a partir de outro arquivo de URL.
urlpatterns = router.urls
