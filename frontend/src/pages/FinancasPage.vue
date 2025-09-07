<template>
  <q-page padding>
    <div class="q-pa-md">
      <!-- Cabeçalho e Botão de Nova Transação -->
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-h4">Finanças</div>
          <div class="text-subtitle1">Visão geral das suas transações</div>
        </div>
        <div class="col-auto">
          <q-btn color="primary" icon="add" label="Nova Transação" @click="abrirDialogNovaTransacao" no-caps />
        </div>
      </div>

      <!-- Cards de Totais -->
      <div class="row q-col-gutter-md q-mb-md">
         <div class="col-12 col-md-6">
          <q-card>
            <q-card-section>
              <div class="text-h6">Faturamento Total (Pago)</div>
              <div class="text-h4 text-positive">{{ formatCurrency(totalPago) }}</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card>
            <q-card-section>
              <div class="text-h6">A Receber (Pendente)</div>
              <div class="text-h4 text-warning">{{ formatCurrency(totalPendente) }}</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Tabela de Transações -->
      <q-card>
        <q-card-section>
          <q-table
            :rows="transacoes"
            :columns="columns"
            row-key="id"
            :loading="loading"
            :filter="filtroStatus"
            :filter-method="filtrarTabela"
            flat
          >
            <template v-slot:top-right>
               <q-select
                v-model="filtroStatus"
                :options="['Todos', 'Pendente', 'Pago']"
                label="Filtrar por Status"
                dense
                outlined
                style="min-width: 150px;"
              />
            </template>

            <template v-slot:body-cell-status="props">
              <q-td :props="props">
                <q-chip
                  :color="getStatusColor(props.row.status)"
                  text-color="white"
                  dense
                  class="text-weight-bold"
                  square
                >
                  {{ props.row.status.charAt(0).toUpperCase() + props.row.status.slice(1) }}
                </q-chip>
              </q-td>
            </template>

            <template v-slot:body-cell-acoes="props">
              <q-td :props="props">
                <q-btn v-if="props.row.status === 'pendente'" class="q-mr-sm" color="positive" icon="o_check_circle" @click="abrirDialogoPagamento(props.row)" dense flat round><q-tooltip>Marcar como Pago</q-tooltip></q-btn>
                <q-btn class="q-mr-sm" dense flat round icon="edit" @click="abrirDialogEditarTransacao(props.row)"><q-tooltip>Editar</q-tooltip></q-btn>
                <q-btn dense flat round icon="delete" @click="confirmarExcluirTransacao(props.row)"><q-tooltip>Excluir</q-tooltip></q-btn>
              </q-td>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </div>

    <!-- Diálogo para Marcar como Pago -->
    <q-dialog v-model="dialogoPagamento">
      <q-card style="width: 400px">
        <q-card-section><div class="text-h6">Confirmar Pagamento</div></q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="pagamentoData.data_pagamento" filled type="date" label="Data do Pagamento" stack-label />
          <q-select class="q-mt-md" v-model="pagamentoData.metodo_pagamento" :options="['Pix', 'Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'Transferência']" filled label="Método de Pagamento" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancelar" v-close-popup />
          <q-btn flat label="Confirmar" color="primary" @click="marcarComoPago" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Diálogo para Nova/Editar Transação -->
    <q-dialog v-model="dialogTransacao">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">{{ modoEdicao ? 'Editar Transação' : 'Nova Transação' }}</div>
        </q-card-section>
        <transacao-form :transacao="transacaoEmEdicao" @transacaoSalva="onTransacaoSalva" />
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from 'boot/axios'
import { Notify, date, Dialog } from 'quasar'
import TransacaoForm from 'src/components/TransacaoForm.vue'

const transacoes = ref([])
const loading = ref(false)
const filtroStatus = ref('Todos')
const dialogoPagamento = ref(false)
const transacaoSelecionada = ref(null)
const pagamentoData = ref({
  data_pagamento: date.formatDate(Date.now(), 'YYYY-MM-DD'),
  metodo_pagamento: 'Pix'
})

// Estado para o CRUD de transações
const dialogTransacao = ref(false)
const transacaoEmEdicao = ref(null)
const modoEdicao = ref(false)

const columns = [
  { name: 'paciente', label: 'Paciente', align: 'left', field: row => row.paciente?.nome_completo || row.agendamento?.paciente?.nome_completo || 'N/A', sortable: true },
  { name: 'servico', label: 'Serviço Prestado', align: 'left', field: row => row.servico_prestado?.nome_servico || 'N/A', sortable: true },
  { name: 'valor', label: 'Valor', align: 'right', field: 'valor_cobrado', format: val => formatCurrency(val), sortable: true },
  { name: 'status', label: 'Status', align: 'center', field: 'status', sortable: true },
  { name: 'data_pagamento', label: 'Data Pagamento', align: 'center', field: 'data_pagamento', format: val => val ? date.formatDate(val, 'DD/MM/YYYY') : '—', sortable: true },
  { name: 'acoes', label: 'Ações', align: 'center' }
]

const totalPago = computed(() => transacoes.value.filter(t => t.status === 'pago').reduce((total, t) => total + parseFloat(t.valor_cobrado), 0))
const totalPendente = computed(() => transacoes.value.filter(t => t.status === 'pendente').reduce((total, t) => total + parseFloat(t.valor_cobrado), 0))

const filtrarTabela = (rows, terms) => {
  if (terms === 'Todos') return rows
  const lowerTerms = terms.toLowerCase()
  return rows.filter(row => row.status === lowerTerms)
}

const fetchTransacoes = async () => {
  loading.value = true
  try {
    const response = await api.get('/transacoes/')
    transacoes.value = response.data
  } catch (error) {
    console.error('Erro ao buscar transações:', error)
    Notify.create({ message: 'Erro ao buscar transações.', color: 'negative', icon: 'error' })
  } finally {
    loading.value = false
  }
}

const abrirDialogoPagamento = (transacao) => {
  transacaoSelecionada.value = transacao
  pagamentoData.value.data_pagamento = date.formatDate(Date.now(), 'YYYY-MM-DD')
  pagamentoData.value.metodo_pagamento = 'Pix'
  dialogoPagamento.value = true
}

const marcarComoPago = async () => {
  if (!transacaoSelecionada.value) return
  try {
    const payload = {
      status: 'pago',
      data_pagamento: pagamentoData.value.data_pagamento,
      metodo_pagamento: pagamentoData.value.metodo_pagamento
    }
    await api.patch(`/transacoes/${transacaoSelecionada.value.id}/`, payload)
    Notify.create({ message: 'Transação atualizada!', color: 'positive', icon: 'check_circle' })
    dialogoPagamento.value = false
    fetchTransacoes()
  } catch (error) {
    console.error('Erro ao atualizar transação:', error)
    Notify.create({ message: 'Erro ao atualizar transação.', color: 'negative', icon: 'error' })
  }
}

// Funções para o CRUD de Transações
const abrirDialogNovaTransacao = () => {
  modoEdicao.value = false
  transacaoEmEdicao.value = null
  dialogTransacao.value = true
}

const abrirDialogEditarTransacao = (transacao) => {
  modoEdicao.value = true
  transacaoEmEdicao.value = transacao
  dialogTransacao.value = true
}

const onTransacaoSalva = () => {
  dialogTransacao.value = false
  fetchTransacoes()
}

const confirmarExcluirTransacao = (transacao) => {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir esta transação? Esta ação não pode ser desfeita.`,
    cancel: true,
    persistent: true,
    ok: { label: 'Excluir', color: 'negative' }
  }).onOk(async () => {
    try {
      await api.delete(`/transacoes/${transacao.id}/`)
      Notify.create({ message: 'Transação excluída com sucesso!', color: 'positive', icon: 'check_circle' })
      fetchTransacoes()
    } catch (error) {
      console.error('Erro ao excluir transação:', error)
      Notify.create({ message: 'Erro ao excluir transação.', color: 'negative', icon: 'error' })
    }
  })
}

const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'R$ 0,00'
  return parseFloat(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const getStatusColor = (status) => {
  const cores = { 'pendente': 'warning', 'pago': 'positive', 'cancelado': 'negative' }
  return cores[status] || 'grey'
}

onMounted(fetchTransacoes)
</script>
