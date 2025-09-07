<template>
  <q-page class="row items-center justify-evenly bg-grey-2">
    <q-card class="q-pa-md shadow-2" style="min-width: 400px;">
      <q-card-section class="text-center">
        <div class="text-grey-9 text-h5 text-weight-bold">Bem-vindo ao ATMA</div>
        <div class="text-grey-8">Faça login para continuar</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="onSubmit">
          <q-input
            dense
            outlined
            v-model="email"
            label="Email"
            type="email"
            lazy-rules
            :rules="[val => !!val || 'O email é obrigatório']"
          />

          <q-input
            class="q-mt-md"
            dense
            outlined
            v-model="password"
            label="Senha"
            type="password"
            lazy-rules
            :rules="[val => !!val || 'A senha é obrigatória']"
          />

          <div v-if="errorMessage" class="q-mt-md text-negative text-center">
            {{ errorMessage }}
          </div>

          <div class="q-mt-lg">
            <q-btn
              label="Login"
              color="primary"
              class="full-width"
              type="submit"
              :loading="loading"
            />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useAuthStore } from 'src/stores/auth'; // <-- Importa nossa store

const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');
const authStore = useAuthStore(); // <-- Inicializa a store

const onSubmit = async () => {
  loading.value = true;
  errorMessage.value = '';

  try {
    const response = await axios.post('http://localhost:8000/api/token/', {
      email: email.value,
      password: password.value,
    });

    // --- CORREÇÃO APLICADA ---
    // Chama a ação de login da nossa store com os tokens recebidos.
    // O alert foi removido.
    authStore.login(response.data.access, response.data.refresh);
    
  } catch (error) {
    console.error('Erro no login:', error.response?.data || error.message);
    if (error.response && error.response.status === 401) {
      errorMessage.value = 'Email ou senha inválidos.';
    } else {
      errorMessage.value = 'Ocorreu um erro. Tente novamente mais tarde.';
    }
  } finally {
    loading.value = false;
  }
};
</script>
