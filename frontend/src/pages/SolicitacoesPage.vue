<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="text-h4 q-mb-md">Solicitações de Pacientes</div>

      <q-card>
        <q-card-section class="row q-col-gutter-md items-center">
            <div class="col-12 col-md-4">
                <q-input dense outlined v-model="filtroPesquisa" label="Buscar por paciente..." clearable />
            </div>
            <div class="col-12 col-md-3">
                <q-select
                v-model="filtroStatus"
                :options="['Todos', 'Pendente', 'Concluído']"
                label="Filtrar por Status"
                dense
                outlined
                />
            </div>
        </q-card-section>

        <q-table
          :rows="solicitacoesFiltradas"
          :columns="colunas"
          row-key="id"
          :loading="loading"
          flat
        >
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-chip
                :color="props.row.status === 'PENDENTE' ? 'orange' : 'green'"
                text-color="white"
                dense
                class="text-weight-bold"
                square
              >
                {{ props.row.status }}
              </q-chip>
            </q-td>
          </template>
           <template v-slot:body-cell-acoes="props">
            <q-td :props="props">
               <q-btn
                  v-if="props.row.status === 'PENDENTE'"
                  color="positive"
                  label="Marcar como Concluído"
                  @click="concluirSolicitacao(props.row)"
                  no-caps
                  dense
                />
            </q-td>
          </template>
           <template v-slot:no-data>
            <div class="full-width row flex-center text-grey q-gutter-sm q-pa-lg">
                <q-icon size="2em" name="o_inbox" />
                <span>Nenhuma solicitação encontrada.</span>
            </div>
          </template>
        </q-table>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from 'boot/axios'
import { Notify, Dialog, date } from 'quasar'

const loading = ref(true)
const solicitacoes = ref([])
const filtroStatus = ref('Pendente')
const filtroPesquisa = ref('')

const colunas = [
  { name: 'paciente', label: 'Paciente', field: row => row.paciente.nome_completo, sortable: true, align: 'left' },
  { name: 'tipo', label: 'Tipo de Solicitação', field: 'tipo_solicitacao', sortable: true, align: 'left' },
  { name: 'data_solicitacao', label: 'Data', field: 'data_solicitacao', format: val => date.formatDate(val, 'DD/MM/YYYY HH:mm'), sortable: true, align: 'left' },
  { name: 'status', label: 'Status', field: 'status', sortable: true, align: 'center' },
  { name: 'acoes', label: 'Ações', align: 'center' }
]

const solicitacoesFiltradas = computed(() => {
  let items = solicitacoes.value

  if (filtroStatus.value !== 'Todos') {
    const statusApi = filtroStatus.value === 'Pendente' ? 'PENDENTE' : 'CONCLUIDO'
    items = items.filter(s => s.status === statusApi)
  }

  if (filtroPesquisa.value) {
    const busca = filtroPesquisa.value.toLowerCase()
    items = items.filter(s => s.paciente.nome_completo.toLowerCase().includes(busca))
  }

  return items
})

async function fetchSolicitacoes() {
  loading.value = true
  try {
    const response = await api.get('/solicitacoes/')
    solicitacoes.value = response.data
  } catch (error) {
    console.error('Erro ao buscar solicitações:', error)
    Notify.create({ color: 'negative', message: 'Falha ao carregar as solicitações.' })
  } finally {
    loading.value = false
  }
}

async function concluirSolicitacao(solicitacao) {
  Dialog.create({
    title: 'Confirmar Conclusão',
    message: `Você confirma que a solicitação de "${solicitacao.tipo_solicitacao}" para ${solicitacao.paciente.nome_completo} foi atendida?`,
    cancel: true,
    persistent: true,
    ok: { label: 'Confirmar', color: 'positive' }
  }).onOk(async () => {
    try {
      await api.patch(`/solicitacoes/${solicitacao.id}/`, { status: 'CONCLUIDO' })
      Notify.create({ color: 'positive', message: 'Solicitação marcada como concluída!' })
      await fetchSolicitacoes()
    } catch (error) {
      console.error('Erro ao concluir solicitação:', error)
      Notify.create({ color: 'negative', message: 'Erro ao atualizar a solicitação.' })
    }
  })
}

onMounted(fetchSolicitacoes)
</script>