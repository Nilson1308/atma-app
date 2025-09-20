<template>
  <q-page padding>
    <q-card>
      <q-card-section>
        <div class="row items-center justify-between q-mb-md">
          <div class="q-gutter-sm">
            <q-btn flat round dense icon="chevron_left" @click="prev" />
            <q-btn flat round dense icon="chevron_right" @click="next" />
            <q-btn dense flat @click="today">Hoje</q-btn>
          </div>
          <div class="text-h5 text-weight-bold">{{ calendarTitle }}</div>
          <div class="q-gutter-sm">
            <q-btn-toggle
              v-model="viewName"
              @update:model-value="changeView"
              toggle-color="primary"
              flat
              size="sm"
              :options="[
                {label: 'Mês', value: 'dayGridMonth'},
                {label: 'Semana', value: 'timeGridWeek'},
                {label: 'Dia', value: 'timeGridDay'}
              ]"
            />
            <q-btn class="q-ml-md" color="primary" icon="add" label="Novo Agendamento" @click="handleDateClick({ date: new Date() })" />
          </div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <FullCalendar
          ref="fullCalendar"
          :options="calendarOptions"
        />
      </q-card-section>
    </q-card>

    <q-dialog v-model="formDialogVisible">
      <q-card style="width: 600px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">{{ agendamentoEmEdicao ? 'Editar Agendamento' : 'Novo Agendamento' }}</div>
        </q-card-section>
        <agendamento-form
          :agendamento="agendamentoEmEdicao"
          :data-selecionada="dataClicada"
          :horarios-trabalho="calendarOptions.businessHours" @agendamento-salvo="onAgendamentoSalvo"
        />
      </q-card>
    </q-dialog>

    <q-dialog v-model="detailsDialogVisible">
       <q-card style="width: 400px;">
        <q-card-section>
          <div class="text-h6">{{ agendamentoSelecionado?.title }}</div>
          <div class="text-subtitle2">{{ agendamentoSelecionado?.extendedProps.paciente_nome }}</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-list dense>
            <q-item>
              <q-item-section avatar><q-icon name="o_calendar_today" /></q-item-section>
              <q-item-section>{{ new Date(agendamentoSelecionado?.start).toLocaleDateString() }}</q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar><q-icon name="o_schedule" /></q-item-section>
              <q-item-section>{{ new Date(agendamentoSelecionado?.start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }} - {{ new Date(agendamentoSelecionado?.end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</q-item-section>
            </q-item>
             <q-item>
              <q-item-section avatar><q-icon name="o_label" /></q-item-section>
              <q-item-section>{{ agendamentoSelecionado?.extendedProps.status }}</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Excluir" color="negative" @click="confirmDelete" />
          <q-btn flat label="Editar" color="primary" @click="openEditDialog" />
          <q-btn flat label="Fechar" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { useAuthStore } from 'src/stores/auth'
import { ref, onMounted, reactive, nextTick } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'
import AgendamentoForm from 'src/components/AgendamentoForm.vue'

const authStore = useAuthStore()
const fullCalendar = ref(null)
const calendarTitle = ref('')
const viewName = ref('timeGridWeek')
const formDialogVisible = ref(false)
const detailsDialogVisible = ref(false)
const agendamentoEmEdicao = ref(null)
const agendamentoSelecionado = ref(null)
const dataClicada = ref(null)

// --- NOVA FUNÇÃO DE VALIDAÇÃO ---
function isHorarioPermitido(data) {
  const diaDaSemana = data.getDay(); // 0=Domingo, 1=Segunda...
  const hora = data.toTimeString().substring(0, 8); // Formato HH:mm:ss

  // Encontra a regra de horário para o dia da semana
  const regraDoDia = calendarOptions.businessHours.find(bh => bh.daysOfWeek.includes(diaDaSemana));

  if (!regraDoDia) {
    return false; // Não há horário de trabalho para este dia
  }

  // Verifica se a hora clicada está dentro do intervalo de trabalho
  return hora >= regraDoDia.startTime && hora < regraDoDia.endTime;
}

const calendarOptions = reactive({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  headerToolbar: false,
  locale: 'pt-br',
  buttonText: { today: 'Hoje', month: 'Mês', week: 'Semana', day: 'Dia' },
  events: [],
  editable: true,
  selectable: true,
  dateClick: handleDateClick,
  eventClick: handleEventClick,
  viewDidMount: (info) => { calendarTitle.value = info.view.title },

  businessHours: [],
  selectConstraint: 'businessHours',

  // --- CORREÇÃO ADICIONADA: Validação fina para seleção ---
  selectAllow: (selectInfo) => {
    return isHorarioPermitido(selectInfo.start);
  },

  slotMinTime: "07:00:00",
  slotMaxTime: "22:00:00",
  allDaySlot: false,
  nowIndicator: true,
  scrollTime: '08:00:00'
})

async function fetchHorariosTrabalho() {
  try {
    const response = await api.get('/horarios-trabalho/')
    const horariosFormatados = response.data
      .filter(h => h.ativo)
      .map(h => {
        const dayOfWeekFC = h.dia_da_semana === 6 ? 0 : h.dia_da_semana + 1;
        return {
          daysOfWeek: [dayOfWeekFC],
          startTime: h.hora_inicio,
          endTime: h.hora_fim
        }
      })
    calendarOptions.businessHours = horariosFormatados
  } catch (error) {
    console.error('Erro ao buscar horários de trabalho:', error)
    Notify.create({ color: 'negative', message: 'Não foi possível carregar os horários de trabalho.' })
  }
}

async function fetchAgendamentos() {
  try {
    const response = await api.get('/agendamentos/')
    
    // Esta verificação agora vai funcionar, pois os dados da assinatura virão da API
    const isPremiumOwner = authStore.user?.funcao === 'proprietario';

    calendarOptions.events = response.data.map(ag => {
      let eventTitle = ag.titulo;

      // Se for proprietário, adiciona o nome do profissional ao evento
      if (isPremiumOwner && ag.profissional !== authStore.user.id) {
        // Pega o primeiro nome
        const nomeProfissional = ag.profissional_nome ? ag.profissional_nome.split(' ')[0] : 'N/A';
        eventTitle = `[${nomeProfissional}] ${ag.titulo}`;
      }

      return {
        id: ag.id,
        title: eventTitle,
        start: ag.data_hora_inicio,
        end: ag.data_hora_fim,
        extendedProps: { ...ag }
      }
    })
  } catch (error) {
    console.error('Erro ao buscar agendamentos:', error)
    Notify.create({ color: 'negative', message: 'Não foi possível carregar os agendamentos.' })
  }
}

// --- FUNÇÃO dateClick ATUALIZADA ---
function handleDateClick(arg) {
  if (isHorarioPermitido(arg.date)) {
    // Se o horário for permitido, abre o formulário
    agendamentoEmEdicao.value = null
    dataClicada.value = arg.date
    formDialogVisible.value = true
  } else {
    // Se não for, exibe um alerta
    Notify.create({
      color: 'negative',
      icon: 'o_block',
      message: 'Este horário está fora do seu expediente de trabalho.',
      position: 'top'
    })
  }
}

function handleEventClick(arg) {
  agendamentoSelecionado.value = arg.event
  detailsDialogVisible.value = true
}

function openEditDialog() {
  agendamentoEmEdicao.value = agendamentoSelecionado.value.extendedProps
  detailsDialogVisible.value = false
  formDialogVisible.value = true
}

function confirmDelete() {
  detailsDialogVisible.value = false
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir o agendamento "${agendamentoSelecionado.value.title}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/agendamentos/${agendamentoSelecionado.value.id}/`)
      Notify.create({ color: 'positive', message: 'Agendamento excluído com sucesso!' })
      fetchAgendamentos()
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error)
      Notify.create({ color: 'negative', message: 'Erro ao excluir agendamento.' })
    }
  })
}

function onAgendamentoSalvo() {
  formDialogVisible.value = false
  fetchAgendamentos()
}

function prev() { fullCalendar.value.getApi().prev(); calendarTitle.value = fullCalendar.value.getApi().view.title }
function next() { fullCalendar.value.getApi().next(); calendarTitle.value = fullCalendar.value.getApi().view.title }
function today() { fullCalendar.value.getApi().today(); calendarTitle.value = fullCalendar.value.getApi().view.title }
function changeView(view) { fullCalendar.value.getApi().changeView(view); calendarTitle.value = fullCalendar.value.getApi().view.title }

onMounted(() => {
  nextTick(async () => {
    await Promise.all([fetchHorariosTrabalho(), fetchAgendamentos()])
  })
})
</script>

<style lang="scss">
.fc .fc-button { padding: 0.4em 0.65em !important; }
.fc-event { cursor: pointer; }
</style>