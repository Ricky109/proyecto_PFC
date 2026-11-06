<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { fmtDateTime, fmtNum, fmtBool, fmtCoords, fmtProb } from '../utils'
import Badge from '../components/Badge.vue'

const props = defineProps({ id: String })
const router = useRouter()
const vehicles = ref([])
const vehicle = ref(null)
const loading = ref(true)
const error = ref('')

async function loadVehicle(id) {
  loading.value = true
  error.value = ''
  try {
    vehicle.value = await api.get(`/vehicles/${id}`)
  } catch (e) {
    vehicle.value = null
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    vehicles.value = await api.get('/vehicles')
  } catch (e) {
    error.value = e.message
    loading.value = false
    return
  }
  if (!props.id) {
    if (vehicles.value.length) router.replace(`/vehiculos/${vehicles.value[0].id}`)
    else loading.value = false
  } else {
    loadVehicle(props.id)
  }
})
watch(() => props.id, (id) => id && loadVehicle(id))
</script>

<template>
  <div class="page narrow">
    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-else-if="loading" class="muted pad">Cargando…</p>
    <p v-else-if="!vehicle" class="alert info">No hay vehículos registrados.</p>

    <template v-else>
      <section class="card">
        <div class="card-head">
          <h2>Vehículo</h2>
          <label class="field inline">Seleccionar vehículo
            <select :value="vehicle.id" @change="(e) => router.push(`/vehiculos/${e.target.value}`)">
              <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.code }} · {{ v.plate }}</option>
            </select>
          </label>
        </div>
        <dl class="grid">
          <div><dt>Código</dt><dd>{{ vehicle.code }}</dd></div>
          <div><dt>Placa</dt><dd>{{ vehicle.plate }}</dd></div>
          <div><dt>IMEI del dispositivo</dt><dd>{{ vehicle.imei }}</dd></div>
          <div><dt>Estado</dt><dd><Badge :value="vehicle.status" /></dd></div>
        </dl>

        <h3>Último registro de telemetría</h3>
        <p v-if="!vehicle.last_telemetry" class="muted">Este vehículo aún no ha enviado telemetría.</p>
        <dl v-else class="grid">
          <div><dt>Recibido</dt><dd>{{ fmtDateTime(vehicle.last_telemetry.received_at) }}</dd></div>
          <div><dt>Velocidad</dt><dd>{{ fmtNum(vehicle.last_telemetry.speed_kmh, 0, 'km/h') }}</dd></div>
          <div><dt>RPM</dt><dd>{{ fmtNum(vehicle.last_telemetry.rpm, 0) }}</dd></div>
          <div><dt>Motor activo</dt><dd>{{ fmtBool(vehicle.last_telemetry.engine_on) }}</dd></div>
          <div><dt>Posición</dt><dd>{{ fmtCoords(vehicle.last_telemetry.latitude, vehicle.last_telemetry.longitude) }}</dd></div>
        </dl>
      </section>

      <section class="card">
        <h2>Eventos y clasificaciones</h2>
        <p v-if="!vehicle.events.length" class="alert info">Este vehículo no tiene eventos registrados.</p>
        <div v-else class="table-wrap">
          <table>
            <thead><tr><th>Fecha y hora</th><th>Tipo</th><th>Gravedad</th><th>Modelo</th><th>Probabilidad</th><th></th></tr></thead>
            <tbody>
              <tr v-for="e in vehicle.events" :key="e.id">
                <td>{{ fmtDateTime(e.occurred_at) }}</td>
                <td>{{ e.event_type_label }}</td>
                <td><Badge :value="e.severity || 'Pendiente'" /></td>
                <td>{{ e.model_version || '—' }}</td>
                <td>{{ fmtProb(e.probability) }}</td>
                <td><router-link :to="`/eventos/${e.id}`">Ver detalle</router-link></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
