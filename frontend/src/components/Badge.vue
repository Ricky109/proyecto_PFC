<script setup>
import { computed } from 'vue'

const props = defineProps({ value: String })
const kind = computed(
  () =>
    ({ leve: 'ok', procesado: 'ok', activo: 'ok', justificado: 'info', moderado: 'warn', pendiente: 'pending', grave: 'danger' })[
      (props.value || '').toLowerCase()
    ] || 'neutral'
)
</script>

<template><span class="badge" :class="kind">{{ value }}</span></template>