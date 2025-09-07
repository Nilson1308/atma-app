import { boot } from 'quasar/wrappers'
import axios from 'axios'
import { useAuthStore } from 'src/stores/auth'

// Cria uma instância do axios com a URL base da nossa API
const api = axios.create({ baseURL: 'http://localhost:8000/api' })

export default boot(({ app }) => {
  // Adiciona um interceptador de requisições
  api.interceptors.request.use(config => {
    const authStore = useAuthStore()
    const token = authStore.accessToken

    // Se o token existir, adiciona ao cabeçalho de autorização
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // Disponibiliza a instância 'api' globalmente no app
  app.config.globalProperties.$api = api
})

// Exporta a instância para podermos usar em qualquer lugar
export { api }

