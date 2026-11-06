<script setup>
import { useRouter } from 'vue-router'
import { auth, logout } from './auth'

const router = useRouter()
function salir() {
  logout()
  router.push('/login')
}
</script>

<template>
  <header v-if="auth.token" class="topbar">
    <span class="brand">TRANSMIND AI</span>
    <nav>
      <router-link to="/eventos">Eventos</router-link>
      <router-link to="/vehiculos">Vehículos</router-link>
    </nav>
    <div class="topbar-right">
      <span class="muted">Analista de flota</span>
      <button class="btn" @click="salir">Salir</button>
    </div>
  </header>
  <main><router-view /></main>
</template>
