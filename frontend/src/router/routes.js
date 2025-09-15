const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [{ path: '', component: () => import('pages/IndexPage.vue') }],
  },
  {
    // Rota da Área Logada (protegida)
    path: '/dashboard',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true }, // <-- Marcamos esta rota como protegida
    children: [
      { path: '', component: () => import('pages/DashboardPage.vue') },
      { path: 'pacientes', component: () => import('pages/PacientesPage.vue') },
      { path: 'pacientes/:id', component: () => import('pages/PacienteDetalhesPage.vue') },
      { path: 'agenda', component: () => import('pages/AgendaPage.vue') },
      { path: 'servicos', component: () => import('pages/ServicosPage.vue') },
      { path: 'financas', component: () => import('pages/FinancasPage.vue') },
      {
        path: 'config',
        component: () => import('pages/ConfiguracoesPage.vue'),
        children: [
          // Redireciona /dashboard/config para /dashboard/config/horarios
          { path: '', redirect: '/dashboard/config/horarios' }, 
          { path: 'horarios', component: () => import('pages/HorariosPage.vue') },
          // Adicionei uma rota de perfil como exemplo para o futuro
          { path: 'perfil', component: () => import('pages/ErrorNotFound.vue') }, // Usando um placeholder por enquanto
        ]
      }
    ]
  },
  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
