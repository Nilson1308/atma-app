<template>
  <q-card-section>
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h6">Base de Conhecimento da IA</div>
        <div class="text-subtitle2">Cadastre aqui as perguntas e respostas que sua secretária virtual deve saber.</div>
      </div>
      <q-btn
        color="primary"
        icon="add"
        label="Nova Categoria"
        @click="abrirDialogoCategoria()"
        no-caps
      />
    </div>

    <div v-if="loading" class="text-center q-pa-lg">
      <q-spinner-dots color="primary" size="40px" />
    </div>

    <div v-else-if="categorias.length === 0" class="text-center text-grey q-pa-lg">
      Nenhuma categoria encontrada. Comece adicionando uma.
    </div>

    <q-list v-else bordered separator>
      <q-expansion-item
        v-for="categoria in categorias"
        :key="categoria.id"
        group="categorias"
        header-class="bg-grey-1"
      >
        <template v-slot:header>
          <q-item-section>
            <q-item-label class="text-weight-bold">{{ categoria.nome }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <div class="q-gutter-sm">
              <q-btn size="sm" flat dense icon="edit" @click.stop="abrirDialogoCategoria(categoria)" />
              <q-btn size="sm" flat dense icon="delete" color="negative" @click.stop="confirmarExcluirCategoria(categoria)" />
              <q-btn size="sm" color="primary" dense icon="add" label="Adicionar Item" @click.stop="abrirDialogoItem(null, categoria.id)" no-caps class="q-ml-md" />
            </div>
          </q-item-section>
        </template>

        <q-list separator>
          <q-item v-if="categoria.itens.length === 0">
            <q-item-section class="q-pa-md text-grey">Nenhum item nesta categoria.</q-item-section>
          </q-item>
          <q-item v-for="item in categoria.itens" :key="item.id">
            <q-item-section>
              <q-item-label class="text-weight-medium text-primary">Intenção: {{ item.intencao_chave }}</q-item-label>
              <q-item-label caption class="q-mt-xs"><span class="text-weight-bold">Exemplos:</span> {{ item.perguntas_exemplo }}</q-item-label>
              <q-item-label caption class="q-mt-xs"><span class="text-weight-bold">Resposta da IA:</span> {{ item.resposta }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn size="sm" flat dense icon="edit" @click="abrirDialogoItem(item)" />
              <q-btn size="sm" flat dense icon="delete" color="negative" @click="confirmarExcluirItem(item)" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-expansion-item>
    </q-list>

    <q-dialog v-model="dialogCategoriaVisivel">
      <categoria-faq-form :categoria="categoriaEmEdicao" @categoriaSalva="onDadosSalvos" />
    </q-dialog>

    <q-dialog v-model="dialogItemVisivel">
      <item-faq-form :item="itemEmEdicao" :categorias="categorias" :categoria-id-inicial="categoriaIdParaNovoItem" @itemSalvo="onDadosSalvos" />
    </q-dialog>

  </q-card-section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Notify, Dialog } from 'quasar'
import CategoriaFaqForm from 'src/components/CategoriaFAQForm.vue'
import ItemFaqForm from 'src/components/ItemFAQForm.vue'

const loading = ref(true)
const categorias = ref([])

const dialogCategoriaVisivel = ref(false)
const categoriaEmEdicao = ref(null)

const dialogItemVisivel = ref(false)
const itemEmEdicao = ref(null)
const categoriaIdParaNovoItem = ref(null)


async function fetchCategorias() {
  loading.value = true
  try {
    const response = await api.get('/faq-categorias/')
    categorias.value = response.data
  } catch (error) {
    console.error('Erro ao buscar categorias do FAQ:', error)
    Notify.create({ color: 'negative', message: 'Falha ao carregar dados do FAQ.' })
  } finally {
    loading.value = false
  }
}

function abrirDialogoCategoria(categoria = null) {
  categoriaEmEdicao.value = categoria
  dialogCategoriaVisivel.value = true
}

function abrirDialogoItem(item = null, categoriaId = null) {
  itemEmEdicao.value = item
  categoriaIdParaNovoItem.value = item ? null : categoriaId
  dialogItemVisivel.value = true
}

function onDadosSalvos() {
  dialogCategoriaVisivel.value = false
  dialogItemVisivel.value = false
  fetchCategorias()
}

function confirmarExcluirCategoria(categoria) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir a categoria "${categoria.nome}" e todos os seus itens? Esta ação não pode ser desfeita.`,
    cancel: true, persistent: true,
    ok: { color: 'negative', label: 'Excluir' }
  }).onOk(async () => {
    try {
      await api.delete(`/faq-categorias/${categoria.id}/`)
      Notify.create({ color: 'positive', message: 'Categoria excluída.' })
      fetchCategorias()
    } catch (error) {
      console.error('Erro ao excluir categoria:', error); // <-- CORREÇÃO APLICADA
      Notify.create({ color: 'negative', message: 'Erro ao excluir categoria.' })
    }
  })
}

function confirmarExcluirItem(item) {
  Dialog.create({
    title: 'Confirmar Exclusão',
    message: `Tem certeza que deseja excluir o item de intenção "${item.intencao_chave}"?`,
    cancel: true, persistent: true,
    ok: { color: 'negative', label: 'Excluir' }
  }).onOk(async () => {
    try {
      await api.delete(`/faq-itens/${item.id}/`)
      Notify.create({ color: 'positive', message: 'Item excluído.' })
      fetchCategorias()
    } catch (error) {
      console.error('Erro ao excluir item:', error); // <-- CORREÇÃO APLICADA
      Notify.create({ color: 'negative', message: 'Erro ao excluir item.' })
    }
  })
}

onMounted(fetchCategorias)
</script>