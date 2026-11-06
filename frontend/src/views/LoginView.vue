<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { setSession } from '../auth'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

function isEmail(v) {
  if (v.length > 120 || /\s/.test(v)) return false
  const at = v.indexOf('@')
  if (at < 1 || at !== v.lastIndexOf('@')) return false
  const domain = v.slice(at + 1)
  const dot = domain.indexOf('.')
  return dot > 0 && !domain.endsWith('.')
}
const emailOk = computed(() => isEmail(email.value))
const canSubmit = computed(() => emailOk.value && password.value.length > 0 && !loading.value)

async function ingresar() {
  error.value = ''
  loading.value = true
  try {
    const r = await api.post('/auth/login', { email: email.value, password: password.value })
    setSession(r.access_token, r.email)
    router.push('/eventos')
  } catch (e) {
    error.value = e.status === 401 ? 'Correo o contraseña incorrectos.' : e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="card login" @submit.prevent="ingresar" novalidate>
      <h1 class="brand big">TRANSMIND AI</h1>
      <p class="muted">Inicia sesión para continuar</p>
      <label class="field">Correo electrónico
        <input v-model.trim="email" type="email" maxlength="120" autocomplete="username" placeholder="analista@empresa.com" />
      </label>
      <label class="field">Contraseña
        <input v-model="password" type="password" autocomplete="current-password" />
      </label>
      <p v-if="email && !emailOk" class="hint">Ingresa un correo válido.</p>
      <p v-if="error" class="alert error">{{ error }}</p>
      <button type="submit" class="btn primary block" :disabled="!canSubmit">{{ loading ? 'Ingresando…' : 'Ingresar' }}</button>
    </form>
  </div>
</template>
