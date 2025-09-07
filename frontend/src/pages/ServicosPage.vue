<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="text-h4">Meus Serviços</div>
          <div class="text-subtitle1">Gerencie seus procedimentos e valores</div>
        </div>
        <div class="col-auto">
          <q-btn color="primary" icon="add" label="Novo Serviço" @click="abrirDialogNovoServico" no-caps />
        </div>
      </div>

      <q-card>
        <q-table
          :rows="servicos"
          :columns="columns"
          row-key="id"
          :loading="loading"
          flat
        >
          <template v-slot:body-cell-acoes="props">
            <q-td :props="props">
              <q-btn dense round flat icon="edit" @click="abrirDialogEditarServico(props.row)"></q-btn>
              <q-btn dense round flat icon="delete" @click="confirmarExcluirServico(props.row)"></q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card>
    </div>

    <!-- Diálogo para Novo/Editar Serviço -->
    <q-dialog v-model="dialogServico">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">{{ modoEdicao ? 'Editar Serviço' : 'Novo Serviço' }}</div>
        </q-card-section>
        <servico-form :servico="servicoEmEdicao" @servicoSalvo="onServicoSalvo" />
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Dialog, Notify } from 'quasar'
import ServicoForm from 'src/components/ServicoForm.vue'

const servicos = ref([])
const loading = ref(false)
const dialogServico = ref(false)
const servicoEmEdicao = ref(null)
const modoEdicao = ref(false)

const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'R$ 0,00'
  return parseFloat(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const columns = [
  { name: 'nome', label: 'Nome', align: 'left', field: 'nome_servico', sortable: true },
  { name: 'duracao', label: 'Duração (min)', align: 'center', field: 'duracao_padrao', sortable: true },
  { name: 'valor', label: 'Valor Padrão', align: 'right', field: 'valor_padrao', format: formatCurrency, sortable: true },
  { name: 'acoes', label: 'Ações', align: 'center' }
]

const fetchServicos = async () => {
  loading.value = true
  try {
    const response = await api.get('/servicos/')
    servicos.value = response.data
  } catch (error) {
    console.error('Erro ao buscar serviços:', error) // <-- CORREÇÃO APLICADA
    Notify.create({
      message: 'Erro ao buscar serviços.',
      color: 'negative',
      icon: 'error'
    })
  } finally {
    loading.value = false
  }
}

const abrirDialogNovoServico = () => {
  modoEdicao.value = false
  servicoEmEdicao.value = null
  dialogServico.value = true
}

const abrirDialogEditarServico = (servico) => {
  modoEdicao.value = true
  servicoEmEdicao.value = servico
  dialogServico.value = true
}

const onServicoSalvo = () => {
  dialogServico.value = false
  fetchServicos()
}

const confirmarExcluirServico = (servico) => {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir o serviço "${servico.nome_servico}"?`,
    cancel: true,
    persistent: true,
    ok: {
      label: 'Excluir',
      color: 'negative'
    }
  }).onOk(async () => {
    try {
      await api.delete(`/servicos/${servico.id}/`)
      Notify.create({
        message: 'Serviço excluído com sucesso!',
        color: 'positive',
        icon: 'check_circle'
      })
      fetchServicos()
    } catch (error) {
      console.error('Erro ao excluir serviço:', error) // <-- CORREÇÃO APLICADA
      Notify.create({
        message: 'Erro ao excluir serviço.',
        color: 'negative',
        icon: 'error'
      })
    }
  })
}

onMounted(fetchServicos)
</script>

