from django.urls import path, include
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter
from .views import ProfissionalViewSet, PacienteViewSet, ProfissionalLogadoView, CategoriaFAQViewSet, ItemFAQViewSet 
from apps.prontuario.urls import router as prontuario_router
from apps.agenda.nested_urls import router as agenda_nested_router
from apps.documentos.urls import router as documentos_router
from apps.financas.nested_urls import router as financas_router

# Router principal para usuários e pacientes
router = DefaultRouter()
router.register(r'profissionais', ProfissionalViewSet, basename='profissional')
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'faq-categorias', CategoriaFAQViewSet, basename='faq-categoria')
router.register(r'faq-itens', ItemFAQViewSet, basename='faq-item')

# Cria um router aninhado para os prontuários, agendamentos e documentos
pacientes_router = routers.NestedSimpleRouter(router, r'pacientes', lookup='paciente')
pacientes_router.registry.extend(prontuario_router.registry)
pacientes_router.registry.extend(agenda_nested_router.registry)
pacientes_router.registry.extend(documentos_router.registry)
pacientes_router.registry.extend(financas_router.registry)

urlpatterns = [
    path('profissionais/me/', ProfissionalLogadoView.as_view(), name='profissional-logado'),
    path('', include(router.urls)),
    path('', include(pacientes_router.urls)),
]
