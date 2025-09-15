<template>
  <q-card-section>
    <div class="text-h6 q-mb-md">Horários Padrão da Semana</div>
    <q-list bordered separator>
      <q-item v-for="dia in semana" :key="dia.id">
        <q-item-section>
          <q-item-label class="text-weight-bold">{{ dia.label }}</q-item-label>
          <q-item-label caption>
            <q-chip
              v-if="getHorarioPorDia(dia.id) && getHorarioPorDia(dia.id).ativo"
              icon="o_check"
              color="positive"
              text-color="white"
              size="sm"
            >
              {{ formatarHora(getHorarioPorDia(dia.id).hora_inicio) }} - {{ formatarHora(getHorarioPorDia(dia.id).hora_fim) }}
            </q-chip>
            <q-chip v-else icon="o_block" color="negative" text-color="white" size="sm">
              Não atende
            </q-chip>
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn flat round icon="edit" @click="abrirDialogoHorario(dia.id)" />
        </q-item-section>
      </q-item>
    </q-list>

    <q-separator class="q-my-lg" />

    <div class="text-h6 q-mb-md">Exceções e Feriados</div>
    <div class="row q-col-gutter-lg">
      <div class="col-12 col-md-5">
        <q-date
          v-model="dataSelecionada"
          :events="datasComExcecao"
          event-color="red"
          minimal
          style="width: 100%;"
          @update:model-value="abrirDialogoExcecao"
        />
        <div class="text-caption q-mt-sm">* Clique em uma data para adicionar ou editar uma exceção.</div>
      </div>
      <div class="col-12 col-md-7">
        <div class="text-subtitle1 q-mb-sm">Próximas exceções cadastradas:</div>
        <q-list bordered separator>
          <q-item v-if="!excecoes.length">
            <q-item-section class="text-grey">Nenhuma exceção encontrada.</q-item-section>
          </q-item>
          <q-item v-for="excecao in excecoes" :key="excecao.id">
            <q-item-section>
              <q-item-label>{{ formatarData(excecao.data) }} - {{ excecao.descricao }}</q-item-label>
              <q-item-label caption>
                <span v-if="excecao.dia_inteiro">Dia todo de folga</span>
                <span v-else>Horário: {{ formatarHora(excecao.hora_inicio) }} - {{ formatarHora(excecao.hora_fim) }}</span>
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn flat round color="negative" icon="delete" @click="confirmarExcluirExcecao(excecao)" />
            </q-item-section>
          </q-item>
        </q-list>
      </div>
    </div>
  </q-card-section>

  <q-dialog v-model="dialogoHorarioAberto">
     <q-card style="width: 400px">
        <q-card-section>
          <div class="text-h6">Editar horário de {{ diaSelecionadoLabel }}</div>
        </q-card-section>
        <q-form @submit.prevent="salvarHorario">
          <q-card-section class="q-gutter-md">
            <q-toggle v-model="formHorario.ativo" label="Atende neste dia" size="lg" />
            <div v-if="formHorario.ativo" class="row q-col-gutter-md">
              <div class="col-6">
                <q-input filled v-model="formHorario.hora_inicio" mask="time" label="Início">
                  <template v-slot:append><q-icon name="access_time" class="cursor-pointer"><q-popup-proxy><q-time v-model="formHorario.hora_inicio" /></q-popup-proxy></q-icon></template>
                </q-input>
              </div>
              <div class="col-6">
                 <q-input filled v-model="formHorario.hora_fim" mask="time" label="Fim">
                  <template v-slot:append><q-icon name="access_time" class="cursor-pointer"><q-popup-proxy><q-time v-model="formHorario.hora_fim" /></q-popup-proxy></q-icon></template>
                </q-input>
              </div>
            </div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat label="Cancelar" v-close-popup />
            <q-btn type="submit" color="primary" label="Salvar" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
  </q-dialog>

  <q-dialog v-model="dialogoExcecaoAberto">
    <q-card style="width: 450px;">
      <q-card-section>
        <div class="text-h6">Configurar Exceção para {{ formExcecao.data ? formatarData(formExcecao.data) : '' }}</div>
      </q-card-section>
      <q-form @submit.prevent="salvarExcecao">
        <q-card-section class="q-gutter-md">
          <q-input v-model="formExcecao.descricao" label="Descrição (Ex: Feriado, Férias) *" dense outlined :rules="[val => !!val || 'Campo obrigatório']"/>
          <q-toggle v-model="formExcecao.dia_inteiro" label="Folga o dia inteiro" size="lg" />
          <div v-if="!formExcecao.dia_inteiro" class="row q-col-gutter-md">
            <div class="col-6"><q-input dense outlined v-model="formExcecao.hora_inicio" mask="time" label="Início"><template v-slot:append><q-icon name="access_time" class="cursor-pointer"><q-popup-proxy><q-time v-model="formExcecao.hora_inicio" /></q-popup-proxy></q-icon></template></q-input></div>
            <div class="col-6"><q-input dense outlined v-model="formExcecao.hora_fim" mask="time" label="Fim"><template v-slot:append><q-icon name="access_time" class="cursor-pointer"><q-popup-proxy><q-time v-model="formExcecao.hora_fim" /></q-popup-proxy></q-icon></template></q-input></div>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancelar" v-close-popup />
          <q-btn type="submit" color="primary" label="Salvar Exceção" :loading="salvando"/>
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>

</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Notify, Dialog, date } from 'quasar'

// --- ESTADO DO COMPONENTE ---
const salvando = ref(false)
const horarios = ref([])
const excecoes = ref([])
const semana = [
  { id: 0, label: 'Segunda-feira' }, { id: 1, label: 'Terça-feira' },
  { id: 2, label: 'Quarta-feira' }, { id: 3, label: 'Quinta-feira' },
  { id: 4, label: 'Sexta-feira' }, { id: 5, label: 'Sábado' },
  { id: 6, label: 'Domingo' },
]

// --- LÓGICA DO DIÁLOGO DE HORÁRIOS ---
const dialogoHorarioAberto = ref(false)
const diaSelecionado = ref(null)
const formHorario = ref({ id: null, dia_da_semana: null, hora_inicio: '09:00', hora_fim: '18:00', ativo: true })

// --- LÓGICA DO DIÁLOGO DE EXCEÇÕES ---
const dialogoExcecaoAberto = ref(false)
const dataSelecionada = ref(null)
const formExcecao = ref({
  id: null, data: null, descricao: '', dia_inteiro: true, hora_inicio: '09:00', hora_fim: '18:00'
})

// --- COMPUTED PROPERTIES ---
const diaSelecionadoLabel = computed(() => semana.find(d => d.id === diaSelecionado.value)?.label || '')
const datasComExcecao = computed(() => excecoes.value.map(e => date.formatDate(e.data, 'YYYY/MM/DD')))

// --- FUNÇÕES DE BUSCA (API) ---
async function buscarDados() {
  await Promise.all([buscarHorarios(), buscarExcecoes()])
}

async function buscarHorarios() {
  try {
    const response = await api.get('/horarios-trabalho/')
    horarios.value = response.data
  } catch (error) {
    console.error('Falha ao carregar horários:', error) // CORREÇÃO APLICADA
    Notify.create({ color: 'negative', message: 'Falha ao carregar horários.' })
  }
}

async function buscarExcecoes() {
  try {
    const response = await api.get('/excecoes-horario/')
    excecoes.value = response.data.sort((a, b) => new Date(a.data) - new Date(b.data))
  } catch (error) {
    console.error('Falha ao carregar exceções:', error) // CORREÇÃO APLICADA
    Notify.create({ color: 'negative', message: 'Falha ao carregar exceções.' })
  }
}

// --- FUNÇÕES DE FORMATAÇÃO E UTILIDADE ---
const getHorarioPorDia = (diaId) => horarios.value.find(h => h.dia_da_semana === diaId)
const formatarHora = (hora) => hora ? hora.substring(0, 5) : ''
const formatarData = (dataStr) => date.formatDate(dataStr, 'DD/MM/YYYY')

// --- FUNÇÕES DE HORÁRIO PADRÃO ---
function abrirDialogoHorario(diaId) {
  diaSelecionado.value = diaId
  const horarioExistente = getHorarioPorDia(diaId)
  formHorario.value = horarioExistente
    ? { ...horarioExistente, hora_inicio: formatarHora(horarioExistente.hora_inicio), hora_fim: formatarHora(horarioExistente.hora_fim) }
    : { id: null, dia_da_semana: diaId, hora_inicio: '09:00', hora_fim: '18:00', ativo: true }
  dialogoHorarioAberto.value = true
}

async function salvarHorario() {
  salvando.value = true
  try {
    const { id, ...payload } = formHorario.value
    if (id) await api.put(`/horarios-trabalho/${id}/`, payload)
    else await api.post('/horarios-trabalho/', payload)
    Notify.create({ color: 'positive', message: 'Horário salvo com sucesso!' })
    dialogoHorarioAberto.value = false
    await buscarHorarios()
  } catch (error) {
    console.error('Erro ao salvar horário:', error) // CORREÇÃO APLICADA
    Notify.create({ color: 'negative', message: 'Erro ao salvar horário.' })
  } finally {
    salvando.value = false
  }
}

// --- FUNÇÕES DE EXCEÇÃO ---
function abrirDialogoExcecao(dataClicada) {
  const dataFormatadaAPI = date.formatDate(dataClicada, 'YYYY-MM-DD')
  const excecaoExistente = excecoes.value.find(e => e.data === dataFormatadaAPI)
  formExcecao.value = excecaoExistente
    ? { ...excecaoExistente }
    : { id: null, data: dataFormatadaAPI, descricao: '', dia_inteiro: true, hora_inicio: '09:00', hora_fim: '18:00' }
  dialogoExcecaoAberto.value = true
}

async function salvarExcecao() {
  salvando.value = true
  try {
    const { id, ...payload } = formExcecao.value
    if (payload.dia_inteiro) {
      payload.hora_inicio = null
      payload.hora_fim = null
    }
    if (id) await api.put(`/excecoes-horario/${id}/`, payload)
    else await api.post('/excecoes-horario/', payload)
    Notify.create({ color: 'positive', message: 'Exceção salva com sucesso!' })
    dialogoExcecaoAberto.value = false
    dataSelecionada.value = null
    await buscarExcecoes()
  } catch (error) {
    console.error('Erro ao salvar exceção:', error) // CORREÇÃO APLICADA
    Notify.create({ color: 'negative', message: 'Erro ao salvar exceção.' })
  } finally {
    salvando.value = false
  }
}

function confirmarExcluirExcecao(excecao) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja remover a exceção de "${excecao.descricao}" do dia ${formatarData(excecao.data)}?`,
    cancel: true, persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/excecoes-horario/${excecao.id}/`)
      Notify.create({ color: 'positive', message: 'Exceção removida.' })
      await buscarExcecoes()
    } catch (error) {
      console.error('Erro ao remover exceção:', error) // CORREÇÃO APLICADA
      Notify.create({ color: 'negative', message: 'Erro ao remover exceção.' })
    }
  })
}

// --- LIFECYCLE HOOK ---
onMounted(buscarDados)
</script>