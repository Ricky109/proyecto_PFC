// Variables más importantes del modelo (gráfica de importancia) que se muestran en el detalle del evento.
// La segunda en importancia ("speed") ya se muestra como "Velocidad", por eso se pasa a la siguiente.
// Para mostrar más, descomenta o agrega líneas: la key es el campo que devuelve la API.
export const CLASSIFICATION_CONTEXT = [
  { key: 'gross_weight_kg', label: 'Peso bruto', unit: 'kg', decimals: 0 },
  { key: 'acceleration_ms2', label: 'Aceleración', unit: 'm/s²', decimals: 2 },
  { key: 'speed_after_kmh', label: 'Velocidad posterior al evento', unit: 'km/h', decimals: 0 }
  // { key: 'heading_change_deg_s', label: 'Cambio de dirección', unit: '°/s', decimals: 1 },
  // { key: 'speed_before_kmh', label: 'Velocidad previa al evento', unit: 'km/h', decimals: 0 },
  // { key: 'road_grade_pct', label: 'Pendiente de la vía', unit: '%', decimals: 1 },
]
