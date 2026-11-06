<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { fmtDateTime, fmtProb, EVENT_TYPES } from '../utils'
import Badge from '../components/Badge.vue'

const pageSize = 10
const tab = ref('eventos') // 'eventos' | 'historial'
const filters = reactive({ desde: '', hasta: '', vehicle_id: '', event_type: '', severity: '', status: '' })
const vehicles = ref([])
const severities = ref([])
const items = ref([])
const total = ref(0)
const page = ref(1)
const summary = ref(null)
const loading = ref(false)
const error = ref('')
let seq = 0

const dateError = computed(() => filters.desde && filters.hasta && filters.desde > filters.hasta)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function params() {
  const p = {}
  for (const k in filters) if (filters[k]) p[k] = filters[k]
  if (tab.value === 'historial') delete p.status
  return p
}

async function load() {
  if (dateError.value) {
    items.value = []; total.value = 0; summary.value = null
    return
  }
  const mine = ++seq
  loading.value = true
  error.value = ''
  try {
    const [s, l] = await Promise.all([
      api.get('/events/summary', params()),
      api.get(tab.value === 'eventos' ? '/events' : '/classifications', { ...params(), page: page.value, page_size: pageSize })
    ])
    if (mine !== seq) return
    summary.value = s; items.value = l.items; total.value = l.total
  } catch (e) {
    if (mine !== seq) return
    error.value = e.message; summary.value = null; items.value = []; total.value = 0
  } finally {
    if (mine === seq) loading.value = false
  }
}

function clearFilters() {
  Object.keys(filters).forEach((k) => (filters[k] = ''))
}

watch(() => [JSON.stringify(filters), tab.value], () => (page.value !== 1 ? (page.value = 1) : load()))
watch(page, load)

onMounted(async () => {
  try { vehicles.value = await api.get('/vehicles') } catch { /* el error se muestra al cargar eventos */ }
  try { severities.value = await api.get('/severities') } catch { /* idem */ }
  load()
})
</script>

<template>
  <div class="page">
    <section v-if="summary" class="cards">
      <div class="stat"><span class="muted">Eventos</span><strong>{{ summary.events }}</strong></div>
      <div class="stat"><span class="muted">Pendientes</span><strong>{{ summary.pending }}</strong></div>
      <div class="stat"><span class="muted">Graves</span><strong>{{ summary.severe }}</strong></div>
      <div class="stat"><span class="muted">Vehículos</span><strong>{{ summary.vehicles }}</strong></div>
    </section>

    <section class="card">
      <div class="tabs">
        <button :class="{ active: tab === 'eventos' }" @click="tab = 'eventos'">Eventos</button>
        <button :class="{ active: tab === 'historial' }" @click="tab = 'historial'">Historial de clasificación</button>
      </div>

      <form class="filters" @submit.prevent>
        <label class="field">Desde<input v-model="filters.desde" type="date" /></label>
        <label class="field">Hasta<input v-model="filters.hasta" type="date" /></label>
        <label class="field">Vehículo
          <select v-model="filters.vehicle_id">
            <option value="">Todos</option>
            <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.code }}</option>
          </select>
        </label>
        <label class="field">Tipo de evento
          <select v-model="filters.event_type">
            <option value="">Todos</option>
            <option v-for="t in EVENT_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </label>
        <label class="field">Gravedad
          <select v-model="filters.severity">
            <option value="">Todas</option>
            <option v-for="s in severities" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label v-if="tab === 'eventos'" class="field">Estado
          <select v-model="filters.status">
            <option value="">Todos</option>
            <option value="pendiente">Pendiente</option>
            <option value="procesado">Procesado</option>
          </select>
        </label>
        <button type="button" class="btn" @click="clearFilters">Limpiar filtros</button>
      </form>

      <p v-if="dateError" class="alert error">La fecha inicial debe ser menor o igual a la final.</p>
      <p v-else-if="error" class="alert error">{{ error }}</p>
      <p v-else-if="loading" class="muted pad">Cargando…</p>
      <p v-else-if="!items.length" class="alert info">No hay resultados para los filtros aplicados.</p>

      <div v-else class="table-wrap">
        <table v-if="tab === 'eventos'">
          <thead><tr><th>Fecha y hora</th><th>Vehículo</th><th>Tipo de evento</th><th>Gravedad</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            <tr v-for="e in items" :key="e.id">
              <td>{{ fmtDateTime(e.occurred_at) }}</td>
              <td><router-link :to="`/vehiculos/${e.vehicle_id}`">{{ e.vehicle_code }}</router-link></td>
              <td>{{ e.event_type_label }}</td>
              <td><Badge v-if="e.severity" :value="e.severity" /><span v-else class="muted">—</span></td>
              <td><Badge :value="e.status" /></td>
              <td><router-link :to="`/eventos/${e.id}`">Ver detalle</router-link></td>
            </tr>
          </tbody>
        </table>

        <table v-else>
          <thead><tr><th>Fecha de clasificación</th><th>Vehículo</th><th>Tipo de evento</th><th>Gravedad</th><th>Modelo</th><th>Probabilidad</th><th></th></tr></thead>
          <tbody>
            <tr v-for="e in items" :key="e.id">
              <td>{{ fmtDateTime(e.classified_at) }}</td>
              <td><router-link :to="`/vehiculos/${e.vehicle_id}`">{{ e.vehicle_code }}</router-link></td>
              <td>{{ e.event_type_label }}</td>
              <td><Badge :value="e.severity" /></td>
              <td>{{ e.model_version }}</td>
              <td>{{ fmtProb(e.probability) }}</td>
              <td><router-link :to="`/eventos/${e.id}`">Ver detalle</router-link></td>
            </tr>
          </tbody>
        </table>

        <div v-if="totalPages > 1" class="pager">
          <button class="btn" :disabled="page <= 1" @click="page--">Anterior</button>
          <span class="muted">Página {{ page }} de {{ totalPages }}</span>
          <button class="btn" :disabled="page >= totalPages" @click="page++">Siguiente</button>
        </div>
      </div>
    </section>
  </div>
</template>