<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-white text-grey-8" height-hint="64">
      <q-toolbar class="q-py-sm">
        <q-btn
          flat
          dense
          round
          @click="toggleLeftDrawer"
          aria-label="Menu"
          icon="menu"
        />

        <q-toolbar-title shrink class="row items-center no-wrap">
          <!-- SVG Logo -->
          <img src="../components/logo_atma-app.png" alt="Logo" style="max-height: 25px">
        </q-toolbar-title>

        <q-space />

        <div class="q-gutter-sm row items-center no-wrap">
          <q-btn round dense flat color="grey-8" icon="notifications">
            <q-badge color="red" text-color="white" floating>
              2
            </q-badge>
            <q-tooltip>Notificações</q-tooltip>
          </q-btn>
          <q-btn round flat>
            <q-avatar size="26px">
              <img src="https://cdn.quasar.dev/img/boy-avatar.png" alt="Avatar do usuário">
            </q-avatar>
            <q-tooltip>Minha Conta</q-tooltip>
          </q-btn>
          <q-btn flat dense round icon="logout" @click="handleLogout">
             <q-tooltip>Sair</q-tooltip>
          </q-btn>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      :width="240"
    >
      <q-scroll-area class="fit">
        <q-list padding>
          <q-item v-for="link in links" :key="link.text" v-ripple clickable :to="link.to">
            <q-item-section avatar>
              <q-icon :name="link.icon" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ link.text }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-separator class="q-my-md" />

        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-page-container class="bg-grey-2">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from 'stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const leftDrawerOpen = ref(false)

const links = ref([
  { icon: 'o_dashboard', text: 'Dashboard', to: '/dashboard' },
  { icon: 'o_people', text: 'Pacientes', to: '/dashboard/pacientes' },
  { icon: 'o_calendar_today', text: 'Agenda', to: '/dashboard/agenda' },
  { icon: 'o_medical_services', text: 'Meus Serviços', to: '/dashboard/servicos' },
  { icon: 'o_paid', text: 'Finanças', to: '/dashboard/financas' },
  { icon: 'o_inbox', text: 'Solicitações', to: '/dashboard/solicitacoes' },
  { icon: 'o_settings', text: 'Configurações', to: '/dashboard/config/horarios' }
])

function toggleLeftDrawer () {
  leftDrawerOpen.value = !leftDrawerOpen.value
}

function handleLogout () {
  authStore.logout()
  router.push('/')
}
</script>

