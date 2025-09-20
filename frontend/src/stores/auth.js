import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { api } from 'boot/axios';

export const useAuthStore = defineStore('auth', () => {
  // --- STATE ---
  const accessToken = ref(localStorage.getItem('accessToken') || null);
  const refreshToken = ref(localStorage.getItem('refreshToken') || null);
  const user = ref(JSON.parse(localStorage.getItem('user')) || null);
  const router = useRouter();

  // --- GETTERS ---
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);
  const conta = computed(() => user.value?.conta);

  // --- ACTIONS ---
  
  async function login(access, refresh) {
    accessToken.value = access;
    refreshToken.value = refresh;
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);

    try {
      // Após o login, busca os dados do usuário
      const response = await api.get('/profissionais/me/');
      user.value = response.data;
      localStorage.setItem('user', JSON.stringify(user.value));
      
      // Redireciona para a página principal
      router.push('/dashboard');
    } catch (error) {
      console.error("Erro ao buscar dados do usuário após login:", error);
      // Se falhar, faz logout para limpar o estado inconsistente
      logout();
    }
  }

  function logout() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    router.push('/');
  }

  // Expõe tudo para ser usado nos componentes
  return {
    accessToken,
    refreshToken,
    user,
    conta,
    isAuthenticated,
    login,
    logout,
  };
});