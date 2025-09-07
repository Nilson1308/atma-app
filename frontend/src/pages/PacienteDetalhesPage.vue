<template>
  <q-page padding>
    <!-- Cabeçalho com dados do Paciente -->
    <div v-if="paciente" class="q-mb-md">
      <div class="row items-center justify-between">
        <div>
          <div class="text-h4">{{ paciente.nome_completo }}</div>
          <div class="text-subtitle1 text-grey-7">{{ paciente.email }} | {{ paciente.contato_telefone }}</div>
        </div>
        <q-btn
          v-if="abaAtual === 'prontuario'"
          color="primary"
          icon="add_comment"
          label="Nova Evolução"
          @click="abrirDialogNovaEntrada"
        />
        <q-btn
          v-if="abaAtual === 'documentos'"
          color="primary"
          icon="o_upload_file"
          label="Adicionar Documento"
          @click="dialogDocumentoVisivel = true"
        />
      </div>
    </div>
    <div v-else class="text-center">
      <q-spinner-dots color="primary" size="40px" />
    </div>

    <!-- Abas de Navegação -->
    <q-card v-if="paciente">
      <q-tabs
        v-model="abaAtual"
        dense
        class="text-grey"
        active-color="primary"
        indicator-color="primary"
        align="justify"
        narrow-indicator
      >
        <q-tab name="prontuario" label="Prontuário" />
        <q-tab name="agendamentos" label="Agendamentos" />
        <q-tab name="documentos" label="Documentos" />
        <q-tab name="financas" label="Finanças" />
        <q-tab name="dados" label="Dados Cadastrais" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="abaAtual" animated>
        <!-- Painel do Prontuário -->
        <q-tab-panel name="prontuario">
          <div class="text-h6 q-mb-md">Histórico do Prontuário</div>
          <q-timeline color="primary">
            <q-timeline-entry
              v-for="entrada in prontuario"
              :key="entrada.id"
              :title="`Entrada de ${entrada.profissional_nome}`"
              :subtitle="new Date(entrada.data_hora).toLocaleString('pt-BR')"
              icon="o_description"
            >
              <div class="q-mb-sm text-caption text-grey" v-if="entrada.agendamento_associado">
                Associado ao atendimento de {{ new Date(getAgendamentoById(entrada.agendamento_associado)?.data_hora_inicio).toLocaleDateString('pt-BR') }}
              </div>
              <div class="q-mb-sm" style="white-space: pre-wrap;">{{ entrada.evolucao }}</div>
              <div class="q-gutter-sm">
                <q-btn size="sm" flat dense round icon="edit" @click="abrirDialogEditarEntrada(entrada)" />
                <q-btn size="sm" flat dense round icon="delete" color="negative" @click="confirmarExcluirEntrada(entrada)" />
              </div>
            </q-timeline-entry>
            <q-timeline-entry v-if="!prontuario.length && !loading" title="Nenhuma entrada encontrada" icon="o_info" />
          </q-timeline>
        </q-tab-panel>

        <!-- Painel de Agendamentos -->
        <q-tab-panel name="agendamentos">
          <div class="text-h6">Histórico de Agendamentos</div>
           <q-list bordered separator>
            <q-item v-for="agendamento in agendamentosPaciente" :key="agendamento.id">
              <q-item-section>
                <q-item-label>{{ agendamento.titulo }}</q-item-label>
                <q-item-label caption>{{ new Date(agendamento.data_hora_inicio).toLocaleString('pt-BR', { dateStyle: 'full', timeStyle: 'short' }) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge :color="getStatusColor(agendamento.status)" :label="agendamento.status" />
              </q-item-section>
            </q-item>
             <q-item v-if="!agendamentosPaciente.length && !loading">
              <q-item-section class="text-grey-7">Nenhum agendamento encontrado para este paciente.</q-item-section>
            </q-item>
          </q-list>
        </q-tab-panel>

        <!-- Painel de Documentos -->
        <q-tab-panel name="documentos">
          <div class="text-h6 q-mb-md">Documentos Anexados</div>
          <q-list bordered separator>
            <q-item v-for="doc in documentos" :key="doc.id">
              <q-item-section avatar>
                <q-icon name="o_description" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ doc.descricao }}</q-item-label>
                <q-item-label caption>Enviado em: {{ new Date(doc.data_upload).toLocaleDateString('pt-BR') }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="q-gutter-sm">
                  <q-btn size="sm" flat dense round icon="o_visibility" :href="`http://localhost:8000${doc.arquivo}`" target="_blank" />
                  <q-btn size="sm" flat dense round icon="delete" color="negative" @click="confirmarExcluirDocumento(doc)" />
                </div>
              </q-item-section>
            </q-item>
            <q-item v-if="!documentos.length && !loading">
              <q-item-section class="text-grey-7">Nenhum documento encontrado.</q-item-section>
            </q-item>
          </q-list>
        </q-tab-panel>

        <!-- Painel de Finanças (Placeholder) -->
        <q-tab-panel name="financas">
           <div class="text-h6">Histórico Financeiro</div>
          <p>Em breve: uma lista com todas as transações (pagas e pendentes) deste paciente.</p>
        </q-tab-panel>

        <!-- Painel de Dados Cadastrais -->
        <q-tab-panel name="dados">
          <paciente-form :paciente="paciente" @paciente-salvo="buscarDados" />
        </q-tab-panel>
      </q-tab-panels>
    </q-card>

    <!-- Diálogo para Upload de Documento -->
    <q-dialog v-model="dialogDocumentoVisivel" @hide="resetFormDocumento">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">Adicionar Novo Documento</div>
        </q-card-section>
        <q-form @submit.prevent="salvarDocumento">
          <q-card-section class="q-gutter-md">
            <q-input
              v-model="formDocumento.descricao"
              label="Descrição do Arquivo *"
              dense
              outlined
              :rules="[val => !!val || 'Campo obrigatório']"
            />
            <q-file
              v-model="formDocumento.arquivo"
              label="Selecione o arquivo *"
              outlined
              dense
              :rules="[val => !!val || 'Campo obrigatório']"
            >
              <template v-slot:prepend>
                <q-icon name="attach_file" />
              </template>
            </q-file>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat label="Cancelar" v-close-popup />
            <q-btn type="submit" color="primary" label="Salvar" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- Diálogo para Nova Entrada/Edição no Prontuário -->
    <q-dialog v-model="dialogEntradaVisivel">
      <q-card style="width: 600px; max-width: 90vw;">
        <q-card-section>
          <div class="text-h6">{{ entradaEmEdicao ? 'Editar Entrada' : 'Nova Entrada no Prontuário' }}</div>
        </q-card-section>
        <q-form @submit.prevent="salvarEntrada">
          <q-card-section class="q-gutter-md">
            <q-editor v-model="textoEvolucao" min-height="10rem" placeholder="Descreva a evolução do paciente aqui..." />
            <q-select
              dense
              outlined
              v-model="agendamentoVinculado"
              :options="opcoesAgendamento"
              label="Associar ao Atendimento (Opcional)"
              emit-value
              map-options
              clearable
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat label="Cancelar" v-close-popup />
            <q-btn type="submit" color="primary" label="Salvar" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'
import PacienteForm from 'src/components/PacienteForm.vue'

const route = useRoute()
const paciente = ref(null)
const prontuario = ref([])
const agendamentosPaciente = ref([])
const documentos = ref([])
const loading = ref(true)
const salvando = ref(false)
const abaAtual = ref('prontuario')
const pacienteId = route.params.id

// Estados para o formulário de documento
const dialogDocumentoVisivel = ref(false)
const formDocumento = ref({
  descricao: '',
  arquivo: null
})

// Estados para o formulário de prontuário
const dialogEntradaVisivel = ref(false)
const textoEvolucao = ref('')
const entradaEmEdicao = ref(null)
const agendamentoVinculado = ref(null)

const opcoesAgendamento = computed(() => {
  return agendamentosPaciente.value
    .filter(ag => ag.status === 'Realizado')
    .map(ag => ({
      label: `${new Date(ag.data_hora_inicio).toLocaleString('pt-BR')} - ${ag.titulo}`,
      value: ag.id
    }))
})

async function buscarDados() {
  loading.value = true
  try {
    const [pacienteResponse, prontuarioResponse, agendamentosResponse, documentosResponse] = await Promise.all([
      api.get(`/pacientes/${pacienteId}/`),
      api.get(`/pacientes/${pacienteId}/prontuario/`),
      api.get(`/pacientes/${pacienteId}/agendamentos/`),
      api.get(`/pacientes/${pacienteId}/documentos/`)
    ]);
    paciente.value = pacienteResponse.data
    prontuario.value = prontuarioResponse.data
    agendamentosPaciente.value = agendamentosResponse.data
    documentos.value = documentosResponse.data
  } catch (error) {
    console.error('Erro ao buscar dados do paciente:', error)
    Notify.create({ color: 'negative', message: 'Falha ao carregar dados do paciente.' })
  } finally {
    loading.value = false
  }
}

function resetFormDocumento() {
  formDocumento.value.descricao = ''
  formDocumento.value.arquivo = null
}

async function salvarDocumento() {
  salvando.value = true
  try {
    const formData = new FormData()
    formData.append('descricao', formDocumento.value.descricao)
    formData.append('arquivo', formDocumento.value.arquivo)

    await api.post(`/pacientes/${pacienteId}/documentos/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    Notify.create({ color: 'positive', message: 'Documento salvo com sucesso!' })
    dialogDocumentoVisivel.value = false
    await buscarDados()
  } catch (error) {
    console.error('Erro ao salvar documento:', error)
    Notify.create({ color: 'negative', message: 'Erro ao salvar documento.' })
  } finally {
    salvando.value = false
  }
}

function confirmarExcluirDocumento(doc) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir o documento "${doc.descricao}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/pacientes/${pacienteId}/documentos/${doc.id}/`)
      Notify.create({ color: 'positive', message: 'Documento excluído com sucesso!' })
      await buscarDados()
    } catch (error) {
      console.error('Erro ao excluir documento:', error)
      Notify.create({ color: 'negative', message: 'Erro ao excluir documento.' })
    }
  })
}

function getStatusColor(status) {
  const cores = { 'Agendado': 'blue', 'Confirmado': 'green', 'Realizado': 'positive', 'Cancelado': 'red', 'Não Compareceu': 'orange' }
  return cores[status] || 'grey'
}

function getAgendamentoById(id) {
  return agendamentosPaciente.value.find(ag => ag.id === id)
}

function abrirDialogNovaEntrada() {
  entradaEmEdicao.value = null
  textoEvolucao.value = ''
  agendamentoVinculado.value = null
  dialogEntradaVisivel.value = true
}

function abrirDialogEditarEntrada(entrada) {
  entradaEmEdicao.value = entrada
  textoEvolucao.value = entrada.evolucao
  agendamentoVinculado.value = entrada.agendamento_associado
  dialogEntradaVisivel.value = true
}

async function salvarEntrada() {
  if (!textoEvolucao.value) {
    Notify.create({ color: 'warning', message: 'O campo de evolução não pode estar vazio.' })
    return
  }
  salvando.value = true
  try {
    const payload = {
      evolucao: textoEvolucao.value,
      agendamento_associado: agendamentoVinculado.value
    }
    if (entradaEmEdicao.value) {
      await api.put(`/pacientes/${pacienteId}/prontuario/${entradaEmEdicao.value.id}/`, payload)
      Notify.create({ color: 'positive', message: 'Entrada atualizada com sucesso!' })
    } else {
      await api.post(`/pacientes/${pacienteId}/prontuario/`, payload)
      Notify.create({ color: 'positive', message: 'Nova entrada salva com sucesso!' })
    }
    dialogEntradaVisivel.value = false
    await buscarDados()
  } catch (error) {
    console.error('Erro ao salvar entrada:', error)
    Notify.create({ color: 'negative', message: 'Erro ao salvar a entrada.' })
  } finally {
    salvando.value = false
  }
}

function confirmarExcluirEntrada(entrada) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: 'Tem certeza que deseja excluir esta entrada do prontuário? Esta ação não pode ser desfeita.',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/pacientes/${pacienteId}/prontuario/${entrada.id}/`)
      Notify.create({ color: 'positive', message: 'Entrada excluída com sucesso!' })
      await buscarDados()
    } catch (error) {
      console.error('Erro ao excluir entrada:', error)
      Notify.create({ color: 'negative', message: 'Erro ao excluir a entrada.' })
    }
  })
}

onMounted(() => {
  buscarDados()
})
</script>
