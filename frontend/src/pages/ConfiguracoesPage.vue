<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="text-h4 q-mb-md">Configurações</div>
      <q-card>
        <q-tabs
          v-model="tab"
          dense
          class="text-grey"
          active-color="primary"
          indicator-color="primary"
          align="left"
          narrow-indicator
        >
          <q-route-tab
            name="horarios"
            label="Meus Horários"
            to="/dashboard/config/horarios"
            exact
          />
          <q-route-tab
            name="perfil"
            label="Meu Perfil"
            to="/dashboard/config/perfil"
            exact
          />
        </q-tabs>

        <q-separator />

        <router-view />
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'

const tab = ref('horarios') // Define 'Meus Horários' como a aba padrão
</script>