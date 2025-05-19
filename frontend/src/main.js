
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/main.css'

const app = createApp(App)

app.config.errorHandler = (err, vm, info) => {
  console.error('Global Vue error:', err, info)
  
  if (vm.$refs.toast) {
    vm.$refs.toast.addNotification(err.message || 'Произошла ошибка в компоненте')
  }
}

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled rejection:', event.reason)
  
  if (event.reason && (event.reason.message === 'Session expired' || 
                       event.reason.message === 'Not authenticated')) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    
    if (router.currentRoute.value.path !== '/login') {
      router.push('/login')
    }
  }

  if (event.reason && event.reason.message) {
    // Ищем корневой экземпляр приложения для показа уведомления
    const appInstance = app._context.app
    if (appInstance && appInstance.$refs.toast) {
      appInstance.$refs.toast.addNotification(event.reason.message)
    } else {
      // Fallback: используем стандартный alert, если toast недоступен
      alert(`Ошибка: ${event.reason.message}`)
    }
  }
})

app.config.globalProperties.$showError = function(message) {
  if (this.$refs.toast) {
    this.$refs.toast.addNotification(message)
  } else {
    console.error('Toast not available:', message)
  }
}

app.config.globalProperties.$showSuccess = function(message) {
  if (this.$refs.toast) {
    this.$refs.toast.addNotification(message, 'success')
  } else {
    console.log('Success:', message)
  }
}

app.use(router)
app.mount('#app')
