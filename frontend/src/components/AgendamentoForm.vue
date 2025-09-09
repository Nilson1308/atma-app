<template>
  <q-form @submit="submitForm">
    <q-card-section>
      <div class="row q-col-gutter-md">

        <!-- Campo Paciente -->
        <div class="col-12">
          <q-select
            filled
            v-model="agendamentoLocal.paciente"
            use-input
            hide-selected
            fill-input
            input-debounce="500"
            label="Paciente *"
            :options="opcoesPacientes"
            @filter="filtrarPacientes"
            option-value="id"
            option-label="nome_completo"
            emit-value
            map-options
            :rules="[val => !!val || 'Paciente é obrigatório']"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  Nenhum paciente encontrado.
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <!-- Campo Serviço -->
        <div class="col-12">
          <q-select
            filled
            v-model="servicoSelecionado"
            use-input
            hide-selected
            fill-input
            input-debounce="500"
            label="Serviço (Opcional)"
            :options="opcoesServicos"
            @filter="filtrarServicos"
            option-value="id"
            option-label="nome_servico"
            clearable
            class="col-12"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  Nenhum serviço encontrado.
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>


        <!-- Campo Título -->
        <div class="col-12">
          <q-input
            filled
            v-model="agendamentoLocal.titulo"
            label="Título *"
            :rules="[val => !!val || 'Título é obrigatório']"
          />
        </div>

        <!-- Campo Data -->
        <div class="col-6">
          <q-input filled v-model="dataAgendamento" mask="##/##/####" :rules="[val => val && val.length === 10 || 'Data inválida']" label="Data *">
            <template v-slot:append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="dataAgendamento" mask="DD/MM/YYYY">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Fechar" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>

        <!-- Campo Status -->
        <div class="col-6">
           <q-select
            filled
            v-model="agendamentoLocal.status"
            :options="opcoesStatus"
            label="Status *"
            :rules="[val => !!val || 'Status é obrigatório']"
          />
        </div>

        <!-- Campo Hora Início -->
        <div class="col-6">
          <q-input filled v-model="horaInicio" mask="time" :rules="['time']" label="Hora Início *">
            <template v-slot:append>
              <q-icon name="access_time" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-time v-model="horaInicio">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Fechar" color="primary" flat />
                    </div>
                  </q-time>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>

        <!-- Campo Hora Fim -->
        <div class="col-6">
          <q-input filled v-model="horaFim" mask="time" :rules="['time']" label="Hora Fim *">
            <template v-slot:append>
              <q-icon name="access_time" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-time v-model="horaFim">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Fechar" color="primary" flat />
                    </div>
                  </q-time>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>

        <!-- Campo Notas -->
        <div class="col-12">
          <q-input
            filled
            v-model="agendamentoLocal.notas_agendamento"
            label="Notas (Opcional)"
            type="textarea"
            autogrow
          />
        </div>

      </div>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Cancelar" color="primary" v-close-popup />
      <q-btn type="submit" label="Salvar" color="primary"/>
    </q-card-actions>
  </q-form>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from 'boot/axios'
import { Notify, date } from 'quasar'

const props = defineProps({
  agendamento: {
    type: Object,
    default: null
  },
  dataSelecionada: {
    type: Date,
    default: null
  }
})

const emit = defineEmits(['agendamentoSalvo'])

const agendamentoLocal = ref({})
const opcoesPacientes = ref([])
const opcoesServicos = ref([])
const servicoSelecionado = ref(null) // Agora vai guardar o objeto completo do serviço

const dataAgendamento = ref(null)
const horaInicio = ref(null)
const horaFim = ref(null)

const opcoesStatus = [ 'Agendado', 'Confirmado', 'Cancelado', 'Realizado', 'Não Compareceu' ]


watch(() => props.agendamento, (novoAgendamento) => {
  if (novoAgendamento) {
    agendamentoLocal.value = { ...novoAgendamento }

    const inicio = new Date(novoAgendamento.data_hora_inicio)
    const fim = new Date(novoAgendamento.data_hora_fim)

    dataAgendamento.value = date.formatDate(inicio, 'DD/MM/YYYY')
    horaInicio.value = date.formatDate(inicio, 'HH:mm')
    horaFim.value = date.formatDate(fim, 'HH:mm')

    if (novoAgendamento.paciente) {
      opcoesPacientes.value = [{ id: novoAgendamento.paciente, nome_completo: novoAgendamento.paciente_nome }]
    }
    
    // --- CORREÇÃO APLICADA AQUI ---
    if (novoAgendamento.servico) {
      // Cria um objeto de serviço para preencher o q-select corretamente.
      const servicoObj = {
        id: novoAgendamento.servico,
        nome_servico: novoAgendamento.servico_nome // Assumindo que o nome do serviço também vem na resposta
      };
      servicoSelecionado.value = servicoObj;
      opcoesServicos.value = [servicoObj];
    } else {
      servicoSelecionado.value = null;
    }

  } else {
    // Reset para um novo agendamento
    agendamentoLocal.value = {
      titulo: '',
      paciente: null,
      status: 'Agendado',
      notas_agendamento: ''
    }
    servicoSelecionado.value = null
    dataAgendamento.value = props.dataSelecionada ? date.formatDate(props.dataSelecionada, 'DD/MM/YYYY') : null;
    horaInicio.value = null
    horaFim.value = null
  }
}, { immediate: true })


watch(servicoSelecionado, (novoServico) => {
  if (!novoServico) return;

  agendamentoLocal.value.titulo = novoServico.nome_servico

  if (horaInicio.value) {
    const [horas, minutos] = horaInicio.value.split(':')
    const dataInicio = new Date()
    dataInicio.setHours(horas, minutos, 0, 0)

    const dataFim = date.addToDate(dataInicio, { minutes: novoServico.duracao_padrao })
    horaFim.value = date.formatDate(dataFim, 'HH:mm')
  }
})

const filtrarPacientes = async (val, update) => {
  if (val.length < 2) {
    update(() => { opcoesPacientes.value = [] })
    return
  }
  try {
    const response = await api.get(`/pacientes/?search=${val}`)
    update(() => {
      opcoesPacientes.value = response.data
    })
  } catch (error) {
    console.error('Erro ao buscar pacientes:', error)
    update(() => { opcoesPacientes.value = [] })
  }
}

const filtrarServicos = async (val, update) => {
  try {
    const response = await api.get(`/servicos/?search=${val}`)
    update(() => {
      opcoesServicos.value = response.data
    })
  } catch (error) {
    console.error('Erro ao buscar serviços:', error)
    update(() => { opcoesServicos.value = [] })
  }
}

const submitForm = async () => {
  try {
    const dataFormatada = date.extractDate(dataAgendamento.value, 'DD/MM/YYYY')
    const dataISO = date.formatDate(dataFormatada, 'YYYY-MM-DD')

    const payload = {
      ...agendamentoLocal.value,
      servico: servicoSelecionado.value ? servicoSelecionado.value.id : null,
      data_hora_inicio: `${dataISO}T${horaInicio.value}:00`,
      data_hora_fim: `${dataISO}T${horaFim.value}:00`
    }

    if (agendamentoLocal.value.id) {
      await api.put(`/agendamentos/${agendamentoLocal.value.id}/`, payload)
    } else {
      await api.post('/agendamentos/', payload)
    }

    Notify.create({
      message: `Agendamento ${agendamentoLocal.value.id ? 'atualizado' : 'criado'} com sucesso!`,
      color: 'positive',
      icon: 'check_circle'
    })

    emit('agendamentoSalvo')

  } catch (error) {
    const errorMessage = error.response?.data ? JSON.stringify(error.response.data) : 'Ocorreu um erro desconhecido.'
    Notify.create({
      message: `Erro ao salvar agendamento: ${errorMessage}`,
      color: 'negative',
      icon: 'error'
    })
    console.error('Erro ao salvar agendamento:', error.response?.data || error)
  }
}

</script>

