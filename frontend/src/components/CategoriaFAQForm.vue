<template>
  <q-card style="width: 400px; max-width: 90vw;">
    <q-card-section>
      <div class="text-h6">{{ isEditing ? 'Editar Categoria' : 'Nova Categoria' }}</div>
    </q-card-section>
    <q-form @submit.prevent="submitForm">
      <q-card-section>
        <q-input
          v-model="formData.nome"
          label="Nome da Categoria *"
          dense
          outlined
          autofocus
          :rules="[val => !!val || 'O nome é obrigatório']"
        />
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
  categoria: Object
})

const emit = defineEmits(['categoriaSalva'])

const loading = ref(false)
const formData = ref({ nome: '' })

const isEditing = computed(() => !!props.categoria)

watch(() => props.categoria, (newVal) => {
  formData.value.nome = newVal ? newVal.nome : ''
}, { immediate: true })

async function submitForm() {
  loading.value = true
  try {
    if (isEditing.value) {
      await api.put(`/faq-categorias/${props.categoria.id}/`, formData.value)
    } else {
      await api.post('/faq-categorias/', formData.value)
    }
    Notify.create({ color: 'positive', message: `Categoria ${isEditing.value ? 'atualizada' : 'criada'} com sucesso!` })
    emit('categoriaSalva')
  } catch (error) {
    console.error('Erro ao salvar categoria:', error); // <-- CORREÇÃO APLICADA
    Notify.create({ color: 'negative', message: 'Erro ao salvar categoria.' })
  } finally {
    loading.value = false
  }
}
</script>