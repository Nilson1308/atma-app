import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

export const useAuthStore = defineStore('auth', () => {
  // --- STATE ---
  // Inicializa o token pegando do localStorage, se existir.
  const accessToken = ref(localStorage.getItem('accessToken') || null);
  const refreshToken = ref(localStorage.getItem('refreshToken') || null);
  const router = useRouter();

  // --- GETTERS ---
  // Um getter computado para saber facilmente se o usuário está logado.
  const isAuthenticated = computed(() => !!accessToken.value);

  // --- ACTIONS ---
  
  /**
   * Processa o login, armazena os tokens e redireciona.
   * @param {string} access - O token de acesso JWT.
   * @param {string} refresh - O token de atualização JWT.
   */
  function login(access, refresh) {
    // Armazena os tokens no estado da store.
    accessToken.value = access;
    refreshToken.value = refresh;

    // Armazena os tokens no localStorage para persistência.
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);

    // TODO: Buscar dados do usuário da API.

    // Redireciona para a página principal após o login.
    router.push('/dashboard'); // Vamos criar esta rota a seguir.
  }

  /**
   * Processa o logout, limpa os dados e redireciona.
   */
  function logout() {
    // Limpa os tokens do estado.
    accessToken.value = null;
    refreshToken.value = null;

    // Remove os tokens do localStorage.
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');

    // Redireciona para a página de login.
    router.push('/');
  }

  // Expõe o estado, getters e actions para serem usados nos componentes.
  return {
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    logout,
  };
});
