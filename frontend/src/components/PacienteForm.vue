<template>
  <q-form @submit.prevent="submitForm">
    <q-card-section>
      <div class="row q-col-gutter-md">
        <div class="col-12">
          <q-input
            label="Nome Completo *"
            v-model="formData.nome_completo"
            filled
            :rules="[val => !!val || 'Campo obrigatório']"
            class="q-mb-md"
          />
        </div>
        <div class="col-12 col-sm-6">
          <q-input
            label="CPF"
            v-model="formData.cpf"
            dense
            outlined
            mask="###.###.###-##"
          />
        </div>
        <div class="col-12 col-sm-6">
          <q-input
            label="Data de Nascimento"
            v-model="formData.data_nascimento"
            dense
            outlined
            mask="##/##/####"
            placeholder="DD/MM/AAAA"
          >
            <template v-slot:append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="formData.data_nascimento" mask="DD/MM/YYYY">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Fechar" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col-12 col-sm-6">
          <q-input
            label="Telefone"
            v-model="formData.contato_telefone"
            dense
            outlined
            mask="(##) #####-####"
          />
        </div>
        <div class="col-12 col-sm-6">
          <q-input
            label="Email"
            v-model="formData.email"
            type="email"
            dense
            outlined
          />
        </div>
        <div class="col-12">
          <q-input
            label="Endereço"
            v-model="formData.endereco"
            type="textarea"
            dense
            outlined
          />
        </div>

        <div class="col-12">
          <q-input
            label="Dia de Cobrança Mensal"
            v-model.number="formData.dia_cobranca"
            type="number"
            dense
            outlined
            hint="Deixe em branco para cobrança imediata após cada consulta."
            :rules="[
              val => (val >= 1 && val <= 31) || !val || 'O dia deve ser entre 1 e 31'
            ]"
          />
        </div>
      </div>
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
import { Notify, date } from 'quasar'

const props = defineProps({
  paciente: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['pacienteSalvo'])

const loading = ref(false)
const formData = ref({
  nome_completo: '',
  cpf: '',
  data_nascimento: '',
  contato_telefone: '',
  email: '',
  endereco: '',
  dia_cobranca: null
})

const isEditing = computed(() => !!props.paciente)

function resetForm() {
  formData.value = {
    nome_completo: '',
    cpf: '',
    data_nascimento: '',
    contato_telefone: '',
    email: '',
    endereco: '',
    dia_cobranca: null
  }
}

watch(() => props.paciente, (newVal) => {
  if (newVal) {
    formData.value = { ...newVal }
    if (formData.value.data_nascimento) {
      // --- CORREÇÃO DE EXIBIÇÃO ---
      // Adiciona um horário para evitar que a data seja interpretada no dia anterior
      // devido ao fuso horário ao carregar os dados.
      const dataAjustada = `${newVal.data_nascimento}T12:00:00`
      const formattedDate = date.formatDate(dataAjustada, 'DD/MM/YYYY')
      formData.value.data_nascimento = formattedDate
    }
  } else {
    resetForm()
  }
}, { immediate: true })


// --- FUNÇÃO CORRIGIDA ---
function formatDataForAPI(data) {
  if (!data || !/^\d{2}\/\d{2}\/\d{4}$/.test(data)) return null
  
  // Converte a data do formato DD/MM/AAAA para um objeto Date
  const dateObject = date.extractDate(data, 'DD/MM/YYYY')
  
  // Formata o objeto Date para o formato AAAA-MM-DD que a API espera
  // A adição do timezone UTC na formatação garante que o dia correto seja enviado
  return date.formatDate(dateObject, 'YYYY-MM-DD')
}

async function submitForm() {
  loading.value = true
  try {
    const dataToSend = {
      ...formData.value,
      data_nascimento: formatDataForAPI(formData.value.data_nascimento),
      dia_cobranca: formData.value.dia_cobranca || null
    }

    if (isEditing.value) {
      await api.put(`/pacientes/${props.paciente.id}/`, dataToSend)
      Notify.create({ color: 'positive', message: 'Paciente atualizado com sucesso!' })
    } else {
      await api.post('/pacientes/', dataToSend)
      Notify.create({ color: 'positive', message: 'Paciente criado com sucesso!' })
    }
    emit('pacienteSalvo')
  } catch (error) {
    console.error('Erro ao salvar paciente:', error)
    Notify.create({ color: 'negative', message: 'Erro ao salvar paciente.' })
  } finally {
    loading.value = false
  }
}
</script>