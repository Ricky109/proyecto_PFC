export const EVENT_TYPES = [
  { value: 'giro_brusco', label: 'Giro brusco' },
  { value: 'frenado_brusco', label: 'Frenado brusco' },
  { value: 'aceleracion_brusca', label: 'Aceleración brusca' },
  { value: 'exceso_velocidad', label: 'Exceso de velocidad' }
]
export const SEVERITIES = ['Leve', 'Moderado', 'Grave']

const p2 = (n) => String(n).padStart(2, '0')

export function fmtDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${String(d.getFullYear()).slice(2)} ${p2(d.getHours())}:${p2(d.getMinutes())}`
}

export function fmtNum(v, decimals = 0, unit = '') {
  if (v === null || v === undefined) return 'No disponible'
  const s = Number(v).toLocaleString('es-PE', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  return unit ? `${s} ${unit}` : s
}

export const fmtProb = (v) => (v === null || v === undefined ? '—' : Number(v).toFixed(2))
export const fmtBool = (v) => (v === null || v === undefined ? 'No disponible' : v ? 'Sí' : 'No')
export const fmtCoords = (lat, lon) =>
  lat === null || lon === null || lat === undefined || lon === undefined
    ? 'No disponible'
    : `${Number(lat).toFixed(4)}, ${Number(lon).toFixed(4)}`
