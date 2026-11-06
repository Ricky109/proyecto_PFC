import { reactive } from 'vue'

function read() {
  try { return JSON.parse(localStorage.getItem('tm_auth')) || {} } catch { return {} }
}
const saved = read()
export const auth = reactive({ token: saved.token || null, email: saved.email || null })

export function setSession(token, email) {
  auth.token = token
  auth.email = email
  localStorage.setItem('tm_auth', JSON.stringify({ token, email }))
}

export function logout() {
  auth.token = null
  auth.email = null
  localStorage.removeItem('tm_auth')
}
