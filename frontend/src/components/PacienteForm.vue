<template>
  <q-form @submit.prevent="submitForm">
    <q-card-section>
      <q-input
        label="Nome Completo *"
        v-model="formData.nome_completo"
        dense
        outlined
        :rules="[val => !!val || 'Campo obrigatório']"
      />
      <q-input
        class="q-mt-md"
        label="CPF"
        v-model="formData.cpf"
        dense
        outlined
        mask="###.###.###-##"
      />
      <q-input
        class="q-mt-md"
        label="Data de Nascimento"
        v-model="formData.data_nascimento"
        dense
        outlined
        mask="##/##/####"
        placeholder="DD/MM/AAAA"
      />
      <q-input
        class="q-mt-md"
        label="Telefone"
        v-model="formData.contato_telefone"
        dense
        outlined
        mask="(##) #####-####"
      />
      <q-input
        class="q-mt-md"
        label="Email"
        v-model="formData.email"
        type="email"
        dense
        outlined
      />
       <q-input
        class="q-mt-md"
        label="Endereço"
        v-model="formData.endereco"
        type="textarea"
        dense
        outlined
      />
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Cancelar" v-close-popup />
      <q-btn
        type="submit"
        color="primary"
        :label="isEditing ? 'Salvar' : 'Criar'"
        :loading="loading"
      />
    </q-card-actions>
  </q-form>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { api } from 'boot/axios'
import { Notify } from 'quasar' // <-- MUDANÇA 1: Importa o Notify diretamente

const props = defineProps({
  paciente: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['pacienteSalvo'])

// const $q = useQuasar() // Removido
const loading = ref(false)
const formData = ref({
  nome_completo: '',
  cpf: '',
  data_nascimento: '',
  contato_telefone: '',
  email: '',
  endereco: '',
})

const isEditing = computed(() => !!props.paciente)

watch(() => props.paciente, (newVal) => {
  if (newVal) {
    formData.value = { ...newVal }
    if (formData.value.data_nascimento) {
      const parts = formData.value.data_nascimento.split('-')
      formData.value.data_nascimento = `${parts[2]}/${parts[1]}/${parts[0]}`
    }
  } else {
    formData.value = { nome_completo: '', cpf: '', data_nascimento: '', contato_telefone: '', email: '', endereco: '' }
  }
}, { immediate: true })


function formatDataForAPI(data) {
  if (!data) return null
  const parts = data.split('/')
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`
  }
  return data
}

async function submitForm() {
  loading.value = true
  try {
    const dataToSend = {
      ...formData.value,
      data_nascimento: formatDataForAPI(formData.value.data_nascimento)
    }

    if (isEditing.value) {
      await api.put(`/pacientes/${props.paciente.id}/`, dataToSend)
      // MUDANÇA 2: Usa Notify.create
      Notify.create({ color: 'positive', message: 'Paciente atualizado com sucesso!' })
    } else {
      await api.post('/pacientes/', dataToSend)
      // MUDANÇA 2: Usa Notify.create
      Notify.create({ color: 'positive', message: 'Paciente criado com sucesso!' })
    }
    emit('pacienteSalvo')
  } catch (error) {
    console.error('Erro ao salvar paciente:', error)
    // MUDANÇA 2: Usa Notify.create
    Notify.create({ color: 'negative', message: 'Erro ao salvar paciente.' })
  } finally {
    loading.value = false
  }
}
</script>
