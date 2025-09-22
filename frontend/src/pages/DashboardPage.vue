<template>
  <q-page padding>
    <div class="q-pa-md">
      <!-- Mensagem de Boas-Vindas -->
      <div class="text-h4">Olá, {{ authStore.user?.nome_completo || 'Profissional' }}!</div>
      <div class="text-subtitle1 text-grey-7 q-mb-lg">
        Bem-vindo(a) à sua conta {{ authStore.conta?.nome_conta || 'Atma App' }}.
      </div>

      <div v-if="loading" class="text-center">
        <q-spinner-dots color="primary" size="40px" />
      </div>

      <div v-else class="row q-col-gutter-lg">
        <!-- Coluna da Esquerda -->
        <div class="col-12 col-lg-8">
          <!-- Card: Agendamentos de Hoje -->
          <q-card class="q-mb-lg">
            <q-card-section>
              <div class="text-h6">Atendimentos de Hoje ({{ new Date().toLocaleDateString('pt-BR') }})</div>
            </q-card-section>
            <q-list separator>
              <q-item v-for="ag in dashboardData.agendamentos_hoje" :key="ag.id" clickable :to="`/dashboard/pacientes/${ag.paciente}`">
                <q-item-section avatar>
                  <q-icon name="o_person" color="primary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ ag.paciente_nome }}</q-item-label>
                  <q-item-label caption>{{ ag.titulo }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <span class="text-weight-bold">{{ new Date(ag.data_hora_inicio).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) }}</span>
                </q-item-section>
              </q-item>
              <q-item v-if="!dashboardData.agendamentos_hoje?.length">
                <q-item-section class="text-grey-7">Nenhum atendimento agendado para hoje.</q-item-section>
              </q-item>
            </q-list>
          </q-card>

          <!-- Card: Próximos 7 Dias -->
          <q-card>
            <q-card-section>
              <div class="text-h6">Próximos 7 Dias</div>
            </q-card-section>
            <q-list separator>
              <q-item v-for="ag in dashboardData.agendamentos_futuros" :key="ag.id" clickable :to="`/dashboard/pacientes/${ag.paciente}`">
                <q-item-section>
                  <q-item-label>{{ ag.paciente_nome }}</q-item-label>
                  <q-item-label caption>{{ ag.titulo }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="text-right">
                    <div class="text-weight-bold">{{ new Date(ag.data_hora_inicio).toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' }) }}</div>
                    <div class="text-caption">{{ new Date(ag.data_hora_inicio).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) }}</div>
                  </div>
                </q-item-section>
              </q-item>
              <q-item v-if="!dashboardData.agendamentos_futuros?.length">
                <q-item-section class="text-grey-7">Nenhum atendimento agendado para os próximos 7 dias.</q-item-section>
              </q-item>
            </q-list>
            <q-card-actions align="right">
              <q-btn flat color="primary" to="/dashboard/agenda" label="Ver Agenda Completa" />
            </q-card-actions>
          </q-card>

          <q-card class="q-mb-lg" v-if="solicitacoesPendentes.length > 0">
            <q-card-section>
              <div class="text-h6 text-orange-8 row items-center">
                <q-icon name="o_priority_high" class="q-mr-sm" />
                Ações Pendentes
              </div>
            </q-card-section>
            <q-list separator>
              <q-item v-for="sol in solicitacoesPendentes" :key="sol.id">
                <q-item-section>
                  <q-item-label>{{ sol.paciente.nome_completo }}</q-item-label>
                  <q-item-label caption>Solicitou: {{ sol.tipo_solicitacao }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                   <q-btn
                      size="sm"
                      color="positive"
                      label="Concluir"
                      @click="concluirSolicitacao(sol)"
                      no-caps
                    />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>

        <!-- Coluna da Direita -->
        <div class="col-12 col-lg-4 q-gutter-lg">
          <!-- Card: Resumo Financeiro -->
          <q-card>
            <q-card-section>
              <div class="text-h6">A Receber</div>
              <div class="text-h4 text-warning">{{ formatCurrency(dashboardData.total_pendente) }}</div>
              <div class="text-subtitle2 text-grey-7">Total em faturas pendentes</div>
            </q-card-section>
            <q-card-actions align="right">
              <q-btn flat color="primary" to="/dashboard/financas" label="Ver Finanças" />
            </q-card-actions>
          </q-card>

          <!-- Card: Aniversariantes do Mês -->
          <q-card>
            <q-card-section>
              <div class="text-h6">Aniversariantes do Mês</div>
            </q-card-section>
             <q-list separator>
              <q-item v-for="p in dashboardData.aniversariantes_mes" :key="p.id" clickable :to="`/dashboard/pacientes/${p.id}`">
                <q-item-section avatar>
                  <q-icon name="o_cake" color="pink" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ p.nome_completo }}</q-item-label>
                </q-item-section>
                 <q-item-section side>
                  <span class="text-weight-bold">{{ new Date(p.data_nascimento).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) }}</span>
                </q-item-section>
              </q-item>
               <q-item v-if="!dashboardData.aniversariantes_mes?.length">
                <q-item-section class="text-grey-7">Nenhum aniversariante este mês.</q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from 'stores/auth'
import { api } from 'boot/axios'
import { Notify } from 'quasar'
import { Dialog } from 'quasar'

const authStore = useAuthStore()
const loading = ref(true)
const dashboardData = ref({})
const solicitacoesPendentes = ref([])

const fetchDashboardData = async () => {
  loading.value = true
  try {
    const [dashboardResponse, solicitacoesResponse] = await Promise.all([
      api.get('/dashboard/'),
      api.get('/solicitacoes/?status=PENDENTE')
    ]);
    dashboardData.value = dashboardResponse.data
    solicitacoesPendentes.value = solicitacoesResponse.data
  } catch (error) {
    console.error('Erro ao buscar dados do dashboard:', error)
    Notify.create({
      message: 'Não foi possível carregar os dados do dashboard.',
      color: 'negative',
      icon: 'error'
    })
  } finally {
    loading.value = false
  }
}

async function concluirSolicitacao(solicitacao) {
  Dialog.create({
    title: 'Confirmar Conclusão',
    message: `Você confirma que a solicitação de "${solicitacao.tipo_solicitacao}" para o paciente ${solicitacao.paciente.nome_completo} foi atendida?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.patch(`/solicitacoes/${solicitacao.id}/`, { status: 'CONCLUIDO' })
      Notify.create({ color: 'positive', message: 'Solicitação marcada como concluída!' })
      await fetchDashboardData() // Atualiza o dashboard
    } catch (error) {
      console.error('Erro ao concluir solicitação:', error)
      Notify.create({ color: 'negative', message: 'Erro ao atualizar a solicitação.' })
    }
  })
}

const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'R$ 0,00'
  return parseFloat(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

onMounted(() => {
  fetchDashboardData()
})
</script>
