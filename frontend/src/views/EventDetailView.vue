<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api'
import { CLASSIFICATION_CONTEXT } from '../contextVariables'
import { fmtDateTime, fmtNum, fmtBool, fmtCoords, fmtProb } from '../utils'
import Badge from '../components/Badge.vue'

const props = defineProps({ id: String })
const ev = ref(null)
const loading = ref(true)
const error = ref('')
const msg = ref(null) // { type: 'success' | 'error', text }
const classifying = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  msg.value = null
  try {
    ev.value = await api.get(`/events/${props.id}`)
  } catch (e) {
    ev.value = null
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function classify() {
  classifying.value = true
  msg.value = null
  try {
    ev.value = await api.post(`/events/${props.id}/classify`)
    msg.value = { type: 'success', text: 'Evento clasificado correctamente.' }
  } catch (e) {
    msg.value = { type: 'error', text: e.message }
  } finally {
    classifying.value = false
  }
}

onMounted(load)
watch(() => props.id, load)
</script>

<template>
  <div class="page narrow">
    <p v-if="loading" class="muted pad">Cargando…</p>
    <template v-else-if="error">
      <p class="alert error">{{ error }}</p>
      <router-link class="btn" to="/eventos">Volver a eventos</router-link>
    </template>

    <section v-else-if="ev" class="card">
      <div class="card-head">
        <h2>Evento #{{ ev.id }}</h2>
        <router-link class="btn" to="/eventos">Volver a eventos</router-link>
      </div>

      <dl class="grid">
        <div><dt>Vehículo</dt><dd><router-link :to="`/vehiculos/${ev.vehicle_id}`">{{ ev.vehicle_code }} · {{ ev.vehicle_plate }}</router-link></dd></div>
        <div><dt>Fecha y hora</dt><dd>{{ fmtDateTime(ev.occurred_at) }}</dd></div>
        <div><dt>Tipo de evento</dt><dd>{{ ev.event_type_label }}</dd></div>
        <div><dt>Estado</dt><dd><Badge :value="ev.status" /></dd></div>
        <div><dt>Ubicación</dt><dd>{{ fmtCoords(ev.latitude, ev.longitude) }}</dd></div>
      </dl>

      <h3>Contexto operativo</h3>
      <dl class="grid">
        <div><dt>Velocidad</dt><dd>{{ fmtNum(ev.speed_kmh, 0, 'km/h') }}</dd></div>
        <div><dt>RPM</dt><dd>{{ fmtNum(ev.rpm, 0) }}</dd></div>
        <div><dt>Motor activo</dt><dd>{{ fmtBool(ev.engine_on) }}</dd></div>
        <div><dt>Datos CAN</dt><dd>{{ ev.can_available ? 'Sí' : 'No disponible' }}</dd></div>
      </dl>

      <h3>Variables relevantes para la clasificación</h3>
      <dl class="grid">
        <div v-for="v in CLASSIFICATION_CONTEXT" :key="v.key">
          <dt>{{ v.label }}</dt>
          <dd>{{ fmtNum(ev[v.key], v.decimals, v.unit) }}</dd>
        </div>
      </dl>

      <h3>Resultado de clasificación</h3>
      <template v-if="ev.status === 'Procesado'">
        <dl class="grid">
          <div><dt>Nivel de gravedad</dt><dd><Badge :value="ev.severity" /></dd></div>
          <div><dt>Versión del modelo</dt><dd>{{ ev.model_version || 'No disponible' }}</dd></div>
          <div><dt>Probabilidad</dt><dd>{{ ev.probability === null ? 'No disponible' : fmtProb(ev.probability) }}</dd></div>
          <div><dt>Fecha de clasificación</dt><dd>{{ fmtDateTime(ev.classified_at) }}</dd></div>
        </dl>
      </template>
      <template v-else>
        <p class="alert warn">Este evento aún no tiene clasificación.</p>
        <button class="btn primary" :disabled="classifying" @click="classify">
          {{ classifying ? 'Clasificando…' : 'Clasificar evento' }}
        </button>
      </template>

      <p v-if="msg" class="alert" :class="msg.type === 'success' ? 'success' : 'error'">{{ msg.text }}</p>
    </section>
  </div>
</template>
