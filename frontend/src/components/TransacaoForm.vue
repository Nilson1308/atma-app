<template>
  <q-form @submit="submitForm">
    <q-card-section class="q-gutter-md">
      <q-select
        filled
        v-model="transacaoLocal.paciente_id"
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
      />
      <q-select
        filled
        v-model="transacaoLocal.servico_prestado_id"
        use-input
        hide-selected
        fill-input
        input-debounce="500"
        label="Serviço Prestado *"
        :options="opcoesServicos"
        @filter="filtrarServicos"
        option-value="id"
        option-label="nome_servico"
        emit-value
        map-options
        :rules="[val => !!val || 'Serviço é obrigatório']"
      />
      <q-input
        filled
        v-model="transacaoLocal.valor_cobrado"
        label="Valor Cobrado (R$) *"
        @update:model-value="formatarValor"
        :rules="[val => !!val || 'O valor é obrigatório']"
      />
      <q-select
        filled
        v-model="transacaoLocal.status"
        :options="['pendente', 'pago', 'cancelado']"
        label="Status *"
        :rules="[val => !!val || 'Status é obrigatório']"
      />
      <q-input
        v-if="transacaoLocal.status === 'pago'"
        v-model="transacaoLocal.data_pagamento"
        filled
        type="date"
        label="Data do Pagamento"
        stack-label
      />
      <q-select
        v-if="transacaoLocal.status === 'pago'"
        v-model="transacaoLocal.metodo_pagamento"
        :options="['Pix', 'Dinheiro', 'Cartão de Crédito', 'Cartão de Débito', 'Transferência']"
        filled
        label="Método de Pagamento"
      />
      <q-input
        filled
        v-model="transacaoLocal.notas"
        label="Notas (Opcional)"
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
  transacao: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['transacaoSalva'])
const transacaoLocal = ref({})
const opcoesPacientes = ref([])
const opcoesServicos = ref([])

watch(() => props.transacao, (novaTransacao) => {
  if (novaTransacao) {
    transacaoLocal.value = { ...novaTransacao, paciente_id: novaTransacao.paciente.id, servico_prestado_id: novaTransacao.servico_prestado.id }
    opcoesPacientes.value = [novaTransacao.paciente]
    opcoesServicos.value = [novaTransacao.servico_prestado]
    formatarValor(transacaoLocal.value.valor_cobrado.toString())
  } else {
    transacaoLocal.value = {
      paciente_id: null,
      servico_prestado_id: null,
      valor_cobrado: '0,00',
      status: 'pendente',
      data_pagamento: null,
      metodo_pagamento: null,
      notas: ''
    }
  }
}, { immediate: true })

const formatarValor = (value) => {
  if (!value) {
    transacaoLocal.value.valor_cobrado = ''
    return
  }
  let numero = value.toString().replace(/\D/g, '').replace(/^0+/, '')
  if (numero.length === 0) { transacaoLocal.value.valor_cobrado = '0,00'; return }
  if (numero.length === 1) { transacaoLocal.value.valor_cobrado = `0,0${numero}`; return }
  if (numero.length === 2) { transacaoLocal.value.valor_cobrado = `0,${numero}`; return }
  const parteInteiraFormatada = numero.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  transacaoLocal.value.valor_cobrado = `${parteInteiraFormatada},${numero.slice(-2)}`
}

const filtrarPacientes = async (val, update) => {
  if (val.length < 2) { update(() => { opcoesPacientes.value = [] }); return }
  try {
    const response = await api.get(`/pacientes/?search=${val}`)
    update(() => { opcoesPacientes.value = response.data })
  } catch (error) { console.error('Erro ao buscar pacientes:', error); update(() => { opcoesPacientes.value = [] }) }
}

const filtrarServicos = async (val, update) => {
  try {
    const response = await api.get(`/servicos/?search=${val}`)
    update(() => { opcoesServicos.value = response.data })
  } catch (error) { console.error('Erro ao buscar serviços:', error); update(() => { opcoesServicos.value = [] }) }
}

const submitForm = async () => {
  try {
    const valorNumerico = transacaoLocal.value.valor_cobrado.replace('.', '').replace(',', '.')
    const payload = { ...transacaoLocal.value, valor_cobrado: valorNumerico }

    if (transacaoLocal.value.id) {
      await api.put(`/transacoes/${transacaoLocal.value.id}/`, payload)
    } else {
      await api.post('/transacoes/', payload)
    }
    Notify.create({ message: `Transação salva com sucesso!`, color: 'positive', icon: 'check_circle' })
    emit('transacaoSalva')
  } catch (error) {
    const errorMessage = error.response?.data ? JSON.stringify(error.response.data) : 'Ocorreu um erro.'
    Notify.create({ message: `Erro ao salvar transação: ${errorMessage}`, color: 'negative', icon: 'error' })
  }
}
</script>

