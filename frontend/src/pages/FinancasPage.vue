<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-h4">Finanças</div>
          <div class="text-subtitle1">Visão geral das suas transações</div>
        </div>
        <div class="col-auto">
          <q-btn color="primary" icon="add" label="Nova Transação" @click="abrirDialogNovaTransacao" no-caps />
        </div>
      </div>

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

      <q-card class="q-mb-md">
        <q-card-section class="row q-col-gutter-md items-center">
          <div class="col-12 col-md-4">
            <q-select
              v-model="filtroPaciente"
              :options="opcoesPacientes"
              label="Filtrar por Paciente"
              option-label="nome_completo"
              dense
              outlined
              clearable
              use-input
              @filter="filtrarPacientes"
            />
          </div>
          <div class="col-12 col-md-3">
            <q-select
              v-model="filtroStatus"
              :options="['Todos', 'Pendente', 'Pago', 'Cancelado']"
              label="Filtrar por Status"
              dense
              outlined
            />
          </div>
          <div class="col-12 col-md-4">
            <q-input dense outlined readonly v-model="filtroPeriodoLabel" label="Filtrar por Período">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filtroPeriodo" range>
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Fechar" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          <div class="col-12 col-md-1 text-center">
            <q-btn flat round icon="o_delete" @click="limparFiltros">
              <q-tooltip>Limpar Filtros</q-tooltip>
            </q-btn>
          </div>
        </q-card-section>
      </q-card>

      <div class="q-mb-md" v-if="selecionadas.length > 0">
        <q-card>
          <q-card-section class="row items-center justify-between">
            <div>
              <span class="text-weight-bold">{{ selecionadas.length }}</span> fatura(s) selecionada(s)
              <span class="text-grey-7 q-ml-sm">(Total: {{ formatCurrency(totalSelecionado) }})</span>
            </div>
            <q-btn
              color="positive"
              icon="o_check_circle"
              label="Marcar Selecionadas como Pagas"
              @click="abrirDialogoPagamentoEmLote"
              no-caps
            />
          </q-card-section>
        </q-card>
      </div>

      <q-card>
        <q-tabs
          v-model="tab"
          dense
          class="text-grey"
          active-color="primary"
          indicator-color="primary"
          align="justify"
        >
          <q-tab name="geral" label="Lançamento Geral" />
          <q-tab name="paciente" label="Lançamento por Paciente" />
        </q-tabs>

        <q-separator />

        <q-tab-panels v-model="tab" animated>
          <q-tab-panel name="geral">
            <q-table
              :rows="transacoesGeral"
              :columns="colunasGeral"
              row-key="id"
              :loading="loading"
              flat
            >
              <template v-slot:body-cell-status="props">
                <q-td :props="props">
                  <q-chip :color="getStatusColor(props.row.status)" text-color="white" dense class="text-weight-bold" square>
                    {{ props.row.status.charAt(0).toUpperCase() + props.row.status.slice(1) }}
                  </q-chip>
                </q-td>
              </template>
               <template v-slot:body-cell-acoes="props">
                <q-td :props="props">
                   <div class="q-gutter-xs">
                      <q-btn v-if="props.row.status === 'pendente'" color="positive" icon="o_check_circle" @click="abrirDialogoPagamento(props.row)" dense flat round><q-tooltip>Marcar como Pago</q-tooltip></q-btn>
                      <q-btn dense flat round icon="edit" @click="abrirDialogEditarTransacao(props.row)"><q-tooltip>Editar</q-tooltip></q-btn>
                      <q-btn dense flat round icon="delete" @click="confirmarExcluirTransacao(props.row)"><q-tooltip>Excluir</q-tooltip></q-btn>
                   </div>
                </q-td>
              </template>
            </q-table>
          </q-tab-panel>

          <q-tab-panel name="paciente">
            <q-list bordered separator>
              <q-expansion-item
                v-for="(meses, pacienteId) in transacoesAgrupadas"
                :key="pacienteId"
                group="pacientes"
                icon="o_person"
                :label="getPacienteNome(pacienteId)"
                header-class="text-primary text-weight-bold"
              >
                <q-expansion-item
                  v-for="(transacoesMes, mes) in meses"
                  :key="mes"
                  group="meses"
                  :label="formatarMesAno(mes)"
                  class="bg-grey-1"
                  dense
                >
                  <template v-slot:header>
                    <q-item-section avatar>
                       <q-checkbox
                        :model-value="getSelecaoStatusMes(transacoesMes)"
                        @update:model-value="toggleSelecaoMes(transacoesMes)"
                        color="primary"
                        indeterminate-value="some"
                      />
                    </q-item-section>
                    <q-item-section>
                      {{ formatarMesAno(mes) }}
                    </q-item-section>
                  </template>

                  <q-list separator>
                    <q-item v-for="transacao in transacoesMes" :key="transacao.id">
                      <q-item-section side top>
                        <q-checkbox v-if="transacao.status === 'pendente'" v-model="selecionadas" :val="transacao.id" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>{{ transacao.servico_prestado.nome_servico }}</q-item-label>
                        <q-item-label caption>
                          <span v-if="transacao.agendamento">Atendimento em: {{ formatDate(transacao.agendamento.data_hora_inicio) }}</span>
                          <span v-else>Lançamento em: {{ formatDate(transacao.data_transacao) }}</span>
                        </q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <div class="text-right">
                          <q-chip :color="getStatusColor(transacao.status)" text-color="white" dense class="text-weight-bold" square>
                            {{ transacao.status.charAt(0).toUpperCase() + transacao.status.slice(1) }}
                          </q-chip>
                          <div class="text-weight-bold q-mt-xs">{{ formatCurrency(transacao.valor_cobrado) }}</div>
                        </div>
                      </q-item-section>
                      <q-item-section side>
                         <div class="q-gutter-xs">
                            <q-btn v-if="transacao.status === 'pendente'" color="positive" icon="o_check_circle" @click="abrirDialogoPagamento(transacao)" dense flat round><q-tooltip>Marcar como Pago</q-tooltip></q-btn>
                            <q-btn dense flat round icon="edit" @click="abrirDialogEditarTransacao(transacao)"><q-tooltip>Editar</q-tooltip></q-btn>
                            <q-btn dense flat round icon="delete" @click="confirmarExcluirTransacao(transacao)"><q-tooltip>Excluir</q-tooltip></q-btn>
                         </div>
                      </q-item-section>
                    </q-item>
                  </q-list>
                </q-expansion-item>
              </q-expansion-item>
              <q-item v-if="Object.keys(transacoesAgrupadas).length === 0 && !loading">
                <q-item-section class="text-grey-7 text-center">Nenhuma transação encontrada.</q-item-section>
              </q-item>
            </q-list>
          </q-tab-panel>
        </q-tab-panels>
      </q-card>
    </div>

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

    <q-dialog v-model="dialogTransacao">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">{{ modoEdicao ? 'Editar Transação' : 'Nova Transação' }}</div>
        </q-card-section>
        <transacao-form :transacao="transacaoEmEdicao" @transacaoSalva="onTransacaoSalva" />
      </q-card>
    </q-dialog>

    <q-dialog v-model="dialogoPagamentoEmLote">
      <q-card style="width: 400px">
        <q-card-section>
          <div class="text-h6">Confirmar Pagamento em Lote</div>
          <div class="text-subtitle2">{{ selecionadas.length }} faturas selecionadas</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="pagamentoData.data_pagamento" filled type="date" label="Data do Pagamento" stack-label />
          <q-select class="q-mt-md" v-model="pagamentoData.metodo_pagamento" :options="['Pix', 'Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'Transferência']" filled label="Método de Pagamento" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancelar" v-close-popup />
          <q-btn flat label="Confirmar Pagamento" color="primary" @click="marcarComoPagoEmLote" />
        </q-card-actions>
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
const tab = ref('geral')

const filtroStatus = ref('Todos')
const filtroPaciente = ref(null)
const filtroPeriodo = ref({ from: null, to: null })
const opcoesPacientes = ref([])

const selecionadas = ref([])
const dialogoPagamento = ref(false)
const dialogoPagamentoEmLote = ref(false)
const transacaoSelecionada = ref(null)
const pagamentoData = ref({
  data_pagamento: date.formatDate(Date.now(), 'YYYY-MM-DD'),
  metodo_pagamento: 'Pix'
})
const dialogTransacao = ref(false)
const transacaoEmEdicao = ref(null)
const modoEdicao = ref(false)

const colunasGeral = [
  { name: 'data', label: 'Data', field: 'data_transacao', format: val => formatDate(val), sortable: true, align: 'left' },
  { name: 'paciente', label: 'Paciente', field: row => row.paciente.nome_completo, sortable: true, align: 'left' },
  { name: 'servico', label: 'Serviço', field: row => row.servico_prestado.nome_servico, sortable: true, align: 'left' },
  { name: 'valor', label: 'Valor', field: 'valor_cobrado', format: val => formatCurrency(val), sortable: true, align: 'right' },
  { name: 'status', label: 'Status', field: 'status', sortable: true, align: 'center' },
  { name: 'acoes', label: 'Ações', align: 'center' }
]

const filtroPeriodoLabel = computed(() => {
  if (!filtroPeriodo.value?.from) return ''
  if (!filtroPeriodo.value.to) return date.formatDate(filtroPeriodo.value.from, 'DD/MM/YYYY')
  return `${date.formatDate(filtroPeriodo.value.from, 'DD/MM/YYYY')} - ${date.formatDate(filtroPeriodo.value.to, 'DD/MM/YYYY')}`
})

const transacoesFiltradas = computed(() => {
  let items = transacoes.value

  if (filtroStatus.value !== 'Todos') {
    items = items.filter(t => t.status === filtroStatus.value.toLowerCase())
  }
  if (filtroPaciente.value) {
    items = items.filter(t => t.paciente.id === filtroPaciente.value.id)
  }

  // LÓGICA DE FILTRO DE DATA CORRIGIDA
  if (filtroPeriodo.value?.from) {
    const fromDate = date.extractDate(filtroPeriodo.value.from, 'YYYY/MM/DD').getTime()
    items = items.filter(t => {
      const transacaoDate = date.extractDate(t.data_transacao, 'YYYY-MM-DD').getTime()
      return transacaoDate >= fromDate
    })
  }
  if (filtroPeriodo.value?.to) {
    const toDate = date.extractDate(filtroPeriodo.value.to, 'YYYY/MM/DD').getTime()
    items = items.filter(t => {
      const transacaoDate = date.extractDate(t.data_transacao, 'YYYY-MM-DD').getTime()
      return transacaoDate <= toDate
    })
  }
  return items
})

const transacoesGeral = computed(() => {
  return [...transacoesFiltradas.value].sort((a, b) => new Date(a.data_transacao) - new Date(b.data_transacao))
})

const transacoesAgrupadas = computed(() => {
  return transacoesFiltradas.value.reduce((acc, transacao) => {
    const pacienteId = transacao.paciente.id;
    const dataBase = transacao.agendamento ? transacao.agendamento.data_hora_inicio : transacao.data_transacao;
    const mesAno = date.formatDate(dataBase, 'YYYY-MM');

    if (!acc[pacienteId]) acc[pacienteId] = {};
    if (!acc[pacienteId][mesAno]) acc[pacienteId][mesAno] = [];
    acc[pacienteId][mesAno].push(transacao);
    return acc;
  }, {});
});

const totalPago = computed(() => transacoes.value.filter(t => t.status === 'pago').reduce((total, t) => total + parseFloat(t.valor_cobrado), 0))
const totalPendente = computed(() => transacoes.value.filter(t => t.status === 'pendente').reduce((total, t) => total + parseFloat(t.valor_cobrado), 0))
const totalSelecionado = computed(() => selecionadas.value.reduce((total, id) => {
  const transacao = transacoes.value.find(t => t.id === id);
  return total + (transacao ? parseFloat(transacao.valor_cobrado) : 0);
}, 0));

const fetchTransacoes = async () => {
  loading.value = true
  try {
    const response = await api.get('/transacoes/')
    transacoes.value = response.data
  } catch (error) { // <-- CORREÇÃO 1
    console.error('Erro ao buscar transações:', error) // Adicionado console.error
    Notify.create({ message: 'Erro ao buscar transações.', color: 'negative' })
  } finally {
    loading.value = false
  }
}

const filtrarPacientes = async (val, update) => {
  try {
    const response = await api.get(`/pacientes/?search=${val}`)
    update(() => { opcoesPacientes.value = response.data })
  } catch (error) { // <-- CORREÇÃO 2
    console.error('Erro ao filtrar pacientes:', error) // Adicionado console.error
    update(() => { opcoesPacientes.value = [] })
  }
}

function getSelecaoStatusMes(transacoesDoMes) {
  const pendentesIds = transacoesDoMes.filter(t => t.status === 'pendente').map(t => t.id)
  if (pendentesIds.length === 0) return false;

  const selecionadasNoMes = selecionadas.value.filter(id => pendentesIds.includes(id))

  if (selecionadasNoMes.length === 0) return false;
  if (selecionadasNoMes.length === pendentesIds.length) return true;
  return 'some'; // Estado indeterminado
}

function toggleSelecaoMes(transacoesDoMes) {
  const pendentesIds = transacoesDoMes.filter(t => t.status === 'pendente').map(t => t.id)
  const todasSelecionadas = getSelecaoStatusMes(transacoesDoMes) === true

  if (todasSelecionadas) {
    // Desmarcar todas
    selecionadas.value = selecionadas.value.filter(id => !pendentesIds.includes(id))
  } else {
    // Marcar todas que ainda não estão na lista
    pendentesIds.forEach(id => {
      if (!selecionadas.value.includes(id)) {
        selecionadas.value.push(id)
      }
    })
  }
}

function limparFiltros() {
  filtroStatus.value = 'Todos'
  filtroPaciente.value = null
  filtroPeriodo.value = { from: null, to: null }
}

function getPacienteNome(pacienteId) {
  const transacao = transacoes.value.find(t => t.paciente.id == pacienteId);
  return transacao ? transacao.paciente.nome_completo : 'Paciente não identificado';
}

function formatarMesAno(mesAno) {
  const [ano, mes] = mesAno.split('-');
  return date.formatDate(new Date(ano, mes - 1), 'MMMM [de] YYYY', { months: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'] }).replace(/^\w/, c => c.toUpperCase());
}

function formatDate(dataStr) {
  return date.formatDate(dataStr, 'DD/MM/YYYY');
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

function abrirDialogoPagamentoEmLote() {
  pagamentoData.value.data_pagamento = date.formatDate(Date.now(), 'YYYY-MM-DD')
  pagamentoData.value.metodo_pagamento = 'Pix'
  dialogoPagamentoEmLote.value = true
}

async function marcarComoPagoEmLote() {
  try {
    const payload = {
      transacao_ids: selecionadas.value,
      data_pagamento: pagamentoData.value.data_pagamento,
      metodo_pagamento: pagamentoData.value.metodo_pagamento
    }
    await api.post('/transacoes/marcar-como-pago-em-lote/', payload)
    Notify.create({ message: `${selecionadas.value.length} transações atualizadas!`, color: 'positive', icon: 'check_circle' })
    dialogoPagamentoEmLote.value = false
    selecionadas.value = [] // Limpa a seleção
    fetchTransacoes() // Atualiza a lista
  } catch (error) {
    console.error('Erro ao atualizar transações em lote:', error)
    Notify.create({ message: 'Erro ao atualizar transações.', color: 'negative', icon: 'error' })
  }
}

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

onMounted(() => {
  fetchTransacoes()
  // Carrega a lista inicial de pacientes para o filtro
  filtrarPacientes('', () => { opcoesPacientes.value = [] }) // <-- CORREÇÃO 3
})
</script>