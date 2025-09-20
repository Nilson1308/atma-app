<template>
  <q-card-section>
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h6">Gerenciamento de Equipe</div>
        <div class="text-subtitle2">Adicione ou remova profissionais da sua conta.</div>
      </div>
      <q-btn
        color="primary"
        icon="add"
        label="Convidar Profissional"
        @click="abrirDialogoNovoProfissional"
      />
    </div>

    <q-table
      :rows="equipe"
      :columns="colunas"
      row-key="id"
      :loading="loading"
      flat
    >
      <template v-slot:body-cell-acoes="props">
        <q-td :props="props">
          <q-btn dense round flat icon="delete" color="negative" @click="confirmarExcluir(props.row)" />
        </q-td>
      </template>
    </q-table>
  </q-card-section>

  <q-dialog v-model="dialogoAberto">
    <q-card style="width: 500px; max-width: 90vw;">
      <q-card-section>
        <div class="text-h6">Convidar Novo Profissional</div>
      </q-card-section>
      <q-form @submit.prevent="salvarNovoProfissional">
        <q-card-section class="q-gutter-md">
          <q-input v-model="form.nome_completo" label="Nome Completo *" dense outlined :rules="[val => !!val || 'Campo obrigatório']" />
          <q-input v-model="form.email" label="Email *" type="email" dense outlined :rules="[val => !!val || 'Campo obrigatório']" />
          <q-input v-model="form.password" label="Senha Temporária *" dense outlined :rules="[val => !!val || 'Campo obrigatório']" hint="O novo profissional deverá alterar a senha no primeiro acesso." />
          <q-input v-model="form.especialidade" label="Especialidade (Opcional)" dense outlined />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancelar" v-close-popup />
          <q-btn type="submit" color="primary" label="Salvar" :loading="salvando" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'

const equipe = ref([])
const loading = ref(true)
const salvando = ref(false)
const dialogoAberto = ref(false)
const form = ref({})

const colunas = [
  { name: 'nome_completo', label: 'Nome', field: 'nome_completo', align: 'left', sortable: true },
  { name: 'email', label: 'Email', field: 'email', align: 'left', sortable: true },
  { name: 'especialidade', label: 'Especialidade', field: 'especialidade', align: 'left' },
  { name: 'acoes', label: 'Ações', align: 'center' }
]

function resetForm() {
  form.value = {
    nome_completo: '',
    email: '',
    password: '',
    especialidade: ''
  }
}

async function fetchEquipe() {
  loading.value = true
  try {
    const response = await api.get('/profissionais/')
    equipe.value = response.data
  } catch (error) {
    // --- CORREÇÃO 1 ---
    console.error('Erro ao carregar a equipe:', error)
    Notify.create({ color: 'negative', message: 'Erro ao carregar a equipe.' })
  } finally {
    loading.value = false
  }
}

function abrirDialogoNovoProfissional() {
  resetForm()
  dialogoAberto.value = true
}

async function salvarNovoProfissional() {
  salvando.value = true
  try {
    await api.post('/profissionais/', form.value)
    Notify.create({ color: 'positive', message: 'Profissional adicionado com sucesso!' })
    dialogoAberto.value = false
    await fetchEquipe()
  } catch (error) {
    const errorMsg = error.response?.data?.email?.[0] || 'Erro ao adicionar profissional.'
    Notify.create({ color: 'negative', message: errorMsg })
  } finally {
    salvando.value = false
  }
}

function confirmarExcluir(profissional) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja remover "${profissional.nome_completo}" da sua equipe?`,
    cancel: true,
    persistent: true,
    ok: { color: 'negative', label: 'Remover' }
  }).onOk(async () => {
    try {
      await api.delete(`/profissionais/${profissional.id}/`)
      Notify.create({ color: 'positive', message: 'Profissional removido.' })
      await fetchEquipe()
    } catch (error) {
      // --- CORREÇÃO 2 ---
      console.error('Erro ao remover profissional:', error)
      Notify.create({ color: 'negative', message: 'Erro ao remover profissional.' })
    }
  })
}

onMounted(() => {
  fetchEquipe()
})
</script>