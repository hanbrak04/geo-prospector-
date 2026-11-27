const API = 'http://localhost:8000/api'

export function getToken() {
  return localStorage.getItem('token')
}

function headers() {
  const h = { 'Content-Type': 'application/json' }
  const t = getToken()
  if (t) h.Authorization = `Token ${t}`
  return h
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, { headers: headers(), ...options })
  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
  return data
}

export const fetchDomaines = () => apiFetch('/domaines/')
export const fetchCommunes = (q) => apiFetch(`/communes/?q=${encodeURIComponent(q)}`)

export function fetchEquipements(bounds, filters) {
  const params = new URLSearchParams({
    bbox: `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`,
  })
  if (filters.d1.length) params.set('d1', filters.d1.join(','))
  if (filters.d2.length) params.set('d2', filters.d2.join(','))
  if (filters.d3.length) params.set('d3', filters.d3.join(','))
  if (filters.communes.length) params.set('communes', filters.communes.join(','))
  return apiFetch(`/equipements/?${params}`)
}

export const login = (username, password) =>
  apiFetch('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) })

export const register = (username, password) =>
  apiFetch('/auth/register/', { method: 'POST', body: JSON.stringify({ username, password }) })

export const logout = () => apiFetch('/auth/logout/', { method: 'POST' })

export const fetchImplantations = () => apiFetch('/implantations/')

export const createImplantation = (data) =>
  apiFetch('/implantations/', { method: 'POST', body: JSON.stringify(data) })

export const updateImplantation = (id, data) =>
  apiFetch(`/implantations/${id}/`, { method: 'PUT', body: JSON.stringify(data) })

export const deleteImplantation = (id) => apiFetch(`/implantations/${id}/`, { method: 'DELETE' })
