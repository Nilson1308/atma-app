<template>
  <q-form @submit="submitForm">
    <q-card-section>
      <q-input
        filled
        v-model="servicoLocal.nome_servico"
        label="Nome do Serviço *"
        :rules="[val => !!val || 'O nome do serviço é obrigatório']"
        class="q-mb-md"
      />
      <q-input
        filled
        v-model="servicoLocal.duracao_padrao"
        label="Duração Padrão (minutos) *"
        type="number"
        :rules="[val => val !== null && val !== '' || 'A duração é obrigatória']"
        class="q-mb-md"
      />
      <q-input
        filled
        v-model="servicoLocal.valor_padrao"
        label="Valor Padrão (R$) *"
        @update:model-value="formatarValor"
        :rules="[val => !!val || 'O valor é obrigatório']"
        class="q-mb-md"
      />
       <q-input
        filled
        v-model="servicoLocal.descricao"
        label="Descrição (Opcional)"
        type="textarea"
        autogrow
      />
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Cancelar" v-close-popup />
      <q-btn type="submit" label="Salvar" color="primary"/>
    </q-card-actions>
  </q-form>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from 'boot/axios'
import { Notify } from 'quasar'

const props = defineProps({
  servico: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['servicoSalvo'])

const servicoLocal = ref({
  nome_servico: '',
  duracao_padrao: null,
  valor_padrao: '0,00',
  descricao: ''
})

const formatarValor = (value) => {
  if (!value) {
    servicoLocal.value.valor_padrao = ''
    return
  }
  // Remove tudo que não for dígito
  let numero = value.toString().replace(/\D/g, '')
  // Remove zeros à esquerda
  numero = numero.replace(/^0+/, '')

  if (numero.length === 0) {
    servicoLocal.value.valor_padrao = '0,00'
    return
  }
  if (numero.length === 1) {
    servicoLocal.value.valor_padrao = `0,0${numero}`
    return
  }
  if (numero.length === 2) {
    servicoLocal.value.valor_padrao = `0,${numero}`
    return
  }

  const parteInteira = numero.slice(0, -2)
  const parteDecimal = numero.slice(-2)
  
  // Adiciona pontos como separadores de milhar
  const parteInteiraFormatada = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

  servicoLocal.value.valor_padrao = `${parteInteiraFormatada},${parteDecimal}`
}


watch(() => props.servico, (novoServico) => {
  if (novoServico) {
    servicoLocal.value = { ...novoServico }
    // Garante que o valor seja formatado corretamente ao editar
    formatarValor(novoServico.valor_padrao.replace('.', ''))
  } else {
    servicoLocal.value = {
      nome_servico: '',
      duracao_padrao: null,
      valor_padrao: '0,00',
      descricao: ''
    }
  }
}, { immediate: true })

const submitForm = async () => {
  try {
    // Converte o valor para o formato numérico correto para a API
    const valorNumerico = servicoLocal.value.valor_padrao.replace('.', '').replace(',', '.')

    const payload = {
      ...servicoLocal.value,
      valor_padrao: valorNumerico,
    }

    if (servicoLocal.value.id) {
      // Edição
      await api.put(`/servicos/${servicoLocal.value.id}/`, payload)
    } else {
      // Criação
      await api.post('/servicos/', payload)
    }
    Notify.create({
      message: `Serviço ${servicoLocal.value.id ? 'atualizado' : 'criado'} com sucesso!`,
      color: 'positive',
      icon: 'check_circle'
    })
    emit('servicoSalvo')
  } catch (error) {
    const errorMessage = error.response?.data ? JSON.stringify(error.response.data) : 'Ocorreu um erro desconhecido.'
    Notify.create({
      message: `Erro ao salvar serviço: ${errorMessage}`,
      color: 'negative',
      icon: 'error'
    })
  }
}

</script>
