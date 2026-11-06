import { auth, logout } from './auth'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function parseDetail(data) {
  if (!data || !data.detail) return 'Ocurrió un error inesperado.'
  if (typeof data.detail === 'string') return data.detail
  return data.detail.map((d) => d.msg).join(' ')
}

async function request(path, { method = 'GET', params, body } = {}) {
  const q = new URLSearchParams(params || {}).toString()
  let res
  try {
    res = await fetch(`/api${path}${q ? '?' + q : ''}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {})
      },
      body: body ? JSON.stringify(body) : undefined
    })
  } catch {
    throw new ApiError('No se pudo conectar con el servidor.', 0)
  }
  if (res.status === 401 && auth.token) { // sesión vencida
    logout()
    window.location.assign('/login')
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(parseDetail(data), res.status)
  return data
}

export const api = {
  get: (path, params) => request(path, { params }),
  post: (path, body) => request(path, { method: 'POST', body })
}
