<template>
  <q-page padding>
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h4">Pacientes</div>
      <q-btn color="primary" icon="add" label="Novo Paciente" @click="openFormDialog()" />
    </div>

    <q-card>
      <q-table
        :rows="pacientes"
        :columns="columns"
        row-key="id"
        :loading="loading"
        flat
        @row-click="onRowClick"
        class="cursor-pointer"
      >
        <template v-slot:body-cell-actions="props">
          <q-td :props="props" @click.stop> <!-- @click.stop evita que o clique na ação dispare o clique na linha -->
            <q-btn dense round flat icon="edit" @click="openFormDialog(props.row)"></q-btn>
            <q-btn dense round flat icon="delete" color="negative" @click="confirmDelete(props.row)"></q-btn>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Diálogo para Adicionar/Editar Paciente -->
    <q-dialog v-model="formDialogVisible">
      <q-card style="width: 600px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">{{ pacienteEmEdicao ? 'Editar Paciente' : 'Novo Paciente' }}</div>
        </q-card-section>
        <paciente-form
          :paciente="pacienteEmEdicao"
          @paciente-salvo="onPacienteSalvo"
        />
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'
import PacienteForm from 'src/components/PacienteForm.vue'
import { useRouter } from 'vue-router' // <-- 1. Importe o useRouter

const router = useRouter() // <-- 2. Inicialize o router
const pacientes = ref([])
const loading = ref(true)
const formDialogVisible = ref(false)
const pacienteEmEdicao = ref(null)

const columns = [
  { name: 'nome_completo', required: true, label: 'Nome Completo', align: 'left', field: 'nome_completo', sortable: true },
  { name: 'cpf', label: 'CPF', align: 'left', field: 'cpf', sortable: true },
  { name: 'contato_telefone', label: 'Telefone', align: 'left', field: 'contato_telefone' },
  { name: 'email', label: 'Email', align: 'left', field: 'email' },
  { name: 'actions', label: 'Ações', align: 'center' }
]

// --- 3. Adicione a função de clique na linha ---
function onRowClick(evt, row) {
  router.push(`/dashboard/pacientes/${row.id}`)
}

async function fetchPacientes() {
  try {
    loading.value = true
    const response = await api.get('/pacientes/')
    pacientes.value = response.data
  } catch (error) {
    console.error('Erro ao buscar pacientes:', error)
    Notify.create({
      color: 'negative',
      position: 'top',
      message: 'Falha ao carregar pacientes. Tente novamente.',
      icon: 'report_problem'
    })
  } finally {
    loading.value = false
  }
}

function openFormDialog(paciente = null) {
  pacienteEmEdicao.value = paciente
  formDialogVisible.value = true
}

function onPacienteSalvo() {
  formDialogVisible.value = false
  fetchPacientes()
}

function confirmDelete(paciente) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir o paciente "${paciente.nome_completo}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/pacientes/${paciente.id}/`)
      Notify.create({ color: 'positive', message: 'Paciente excluído com sucesso!' })
      fetchPacientes()
    } catch (error) {
      console.error('Erro ao excluir paciente:', error)
      Notify.create({ color: 'negative', message: 'Erro ao excluir paciente.' })
    }
  })
}

onMounted(() => {
  fetchPacientes()
})
</script>
