<template>
  <q-card-section>
    <div v-if="loading" class="text-center q-pa-lg">
      <q-spinner-dots color="primary" size="40px" />
    </div>
    <q-form v-else @submit.prevent="salvarPerfil">
      <div class="text-h6 q-mb-md">Perfil da Clínica/Consultório</div>
      <div class="row q-col-gutter-lg">
        <div class="col-12 col-md-8 q-gutter-y-md">
          <q-input
            v-model="form.endereco_completo"
            label="Endereço Completo"
            outlined
            dense
          />
          <q-input
            v-model="form.site_url"
            label="Site"
            placeholder="https://www.seusite.com.br"
            outlined
            dense
          />
          <q-input
            v-model="form.instagram_handle"
            label="Usuário do Instagram"
            prefix="@"
            outlined
            dense
          />
          <q-input
            v-model="form.bio"
            label="Bio / Breve Descrição"
            type="textarea"
            outlined
            autogrow
            hint="Fale um pouco sobre você ou sua clínica. Esta informação pode ser usada pela IA."
          />
        </div>
        <div class="col-12 col-md-4 text-center">
            <q-img
                :src="logotipoUrl"
                style="width: 150px; height: 150px; border-radius: 50%; border: 1px solid #ddd"
                fit="cover"
            >
                <div v-if="!logotipoUrl" class="absolute-full text-subtitle2 flex flex-center">
                    Logotipo
                </div>
            </q-img>
             <q-file
                v-model="novoLogotipo"
                label="Alterar Logotipo"
                accept="image/*"
                outlined
                dense
                class="q-mt-md"
                @update:model-value="previewLogo"
            />
        </div>
      </div>
       <div class="row q-mt-lg">
          <div class="col-12">
            <q-btn
              type="submit"
              color="primary"
              label="Salvar Alterações"
              :loading="salvando"
              no-caps
            />
          </div>
        </div>
    </q-form>
  </q-card-section>
</template>

<script setup>
// A CORREÇÃO ESTÁ AQUI: 'computed' foi removido da importação.
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { Notify } from 'quasar'

const loading = ref(true)
const salvando = ref(false)
const form = ref({})
const novoLogotipo = ref(null)
const logotipoUrl = ref(null)

const baseURL = 'http://localhost:8000'

async function buscarPerfil() {
  loading.value = true
  try {
    const response = await api.get('/perfil-clinica/')
    form.value = response.data
    if (response.data.logotipo) {
      logotipoUrl.value = `${baseURL}${response.data.logotipo}`
    }
  } catch (error) {
    console.error('Erro ao buscar perfil:', error)
    Notify.create({ color: 'negative', message: 'Falha ao carregar o perfil.' })
  } finally {
    loading.value = false
  }
}

function previewLogo(file) {
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      logotipoUrl.value = e.target.result;
    };
    reader.readAsDataURL(file);
  }
}

async function salvarPerfil() {
  salvando.value = true
  try {
    const formData = new FormData()
    // Adiciona apenas os campos que não são o arquivo
    Object.keys(form.value).forEach(key => {
      if (key !== 'logotipo' && form.value[key] !== null) {
        formData.append(key, form.value[key])
      }
    });

    if (novoLogotipo.value) {
      formData.append('logotipo', novoLogotipo.value)
    }

    // Usamos PATCH para permitir atualizações parciais
    await api.patch('/perfil-clinica/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    Notify.create({ color: 'positive', message: 'Perfil salvo com sucesso!' })
    novoLogotipo.value = null // Reseta o campo do arquivo
    await buscarPerfil() // Re-busca os dados para garantir a consistência
  } catch (error) {
    console.error('Erro ao salvar perfil:', error.response?.data || error)
    Notify.create({ color: 'negative', message: 'Erro ao salvar o perfil.' })
  } finally {
    salvando.value = false
  }
}

onMounted(buscarPerfil)
</script>