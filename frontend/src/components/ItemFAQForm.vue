<template>
  <q-card style="width: 600px; max-width: 90vw;">
    <q-card-section>
      <div class="text-h6">{{ isEditing ? 'Editar Item do FAQ' : 'Novo Item no FAQ' }}</div>
    </q-card-section>
    <q-form @submit.prevent="submitForm">
      <q-card-section class="q-gutter-md">
        <q-select
          v-model="formData.categoria"
          :options="categorias"
          label="Categoria *"
          option-value="id"
          option-label="nome"
          emit-value
          map-options
          dense
          outlined
          :rules="[val => !!val || 'Campo obrigatório']"
        />
        <q-input
          v-model="formData.intencao_chave"
          label="Intenção Chave *"
          dense
          outlined
          hint="Palavra-chave para a IA (ex: verificar_convenios, horario_funcionamento)"
          :rules="[val => !!val || 'Campo obrigatório']"
        />
        <q-input
          v-model="formData.perguntas_exemplo"
          label="Perguntas de Exemplo *"
          type="textarea"
          dense
          outlined
          hint="Exemplos de perguntas dos pacientes, separadas por ponto e vírgula (;)"
          :rules="[val => !!val || 'Campo obrigatório']"
        />
        <q-input
          v-model="formData.resposta"
          label="Resposta da IA *"
          type="textarea"
          autogrow
          dense
          outlined
          hint="A resposta exata que a IA deve fornecer."
          :rules="[val => !!val || 'Campo obrigatório']"
        />
        <div class="q-pa-sm text-caption bg-grey-2 rounded-borders">
            <strong>Dica:</strong> Você pode usar as chaves abaixo para que a IA preencha com os dados da sua clínica:
            <ul class="q-ma-none q-pl-md q-mt-xs">
                <li><code>[nome_clinica]</code></li>
                <li><code>[endereco_completo]</code></li>
                <li><code>[lista_servicos]</code></li>
                <li><code>[horario_funcionamento]</code></li>
            </ul>
        </div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="Cancelar" v-close-popup />
        <q-btn type="submit" color="primary" :label="isEditing ? 'Salvar' : 'Criar'" :loading="loading" />
      </q-card-actions>
    </q-form>
  </q-card>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { api } from 'boot/axios'
import { Notify } from 'quasar'

const props = defineProps({
  item: Object,
  categorias: Array,
  categoriaIdInicial: Number
})

const emit = defineEmits(['itemSalvo'])

const loading = ref(false)
const formData = ref({})

const isEditing = computed(() => !!props.item)

watch(() => props.item, (newVal) => {
  if (newVal) {
    formData.value = { ...newVal }
  } else {
    formData.value = {
      categoria: props.categoriaIdInicial || null,
      intencao_chave: '',
      perguntas_exemplo: '',
      resposta: ''
    }
  }
}, { immediate: true })

async function submitForm() {
  loading.value = true
  try {
    if (isEditing.value) {
      await api.put(`/faq-itens/${props.item.id}/`, formData.value)
    } else {
      await api.post('/faq-itens/', formData.value)
    }
    Notify.create({ color: 'positive', message: `Item ${isEditing.value ? 'atualizado' : 'criado'} com sucesso!` })
    emit('itemSalvo')
  } catch (error) {
    console.error('Erro ao salvar o item:', error); // <-- CORREÇÃO APLICADA
    Notify.create({ color: 'negative', message: 'Erro ao salvar o item.' })
  } finally {
    loading.value = false
  }
}
</script>