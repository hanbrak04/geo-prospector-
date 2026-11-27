// Tous les appels HTTP vers l'API Django sont centralises ici.
// Base relative '/api' : en dev, le proxy Vite (vite.config.js) la relaie
// vers http://backend:8000 -> front et API partagent la meme URL (localhost:5173),
// ce qui evite tout probleme de CORS.
const API = '/api'

export function getToken() {
  return localStorage.getItem('token')   // token stocke a la connexion (voir App.jsx)
}

function headers() {
  const h = { 'Content-Type': 'application/json' }
  const t = getToken()
  // authentification par token : chaque requete prouve qui on est (stateless)
  if (t) h.Authorization = `Token ${t}`
  return h
}

// Wrapper fetch commun : injecte les headers, parse le JSON,
// transforme les erreurs HTTP en exceptions JS exploitables
export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, { headers: headers(), ...options })
  if (res.status === 204) return null   // DELETE / logout : pas de corps
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
  return data
}

// ── Referentiels (lecture seule) ────────────────────────────────
export const fetchDomaines = () => apiFetch('/domaines/')           // arbre des domaines (3 niveaux)
export const fetchCommunes = (q) => apiFetch(`/communes/?q=${encodeURIComponent(q)}`)
export const fetchAdresses = (q, type) =>                          // geocodage BAN via le backend
  apiFetch(`/geocode/?q=${encodeURIComponent(q)}${type ? `&type=${type}` : ''}`)
export const fetchEquipementsByNom = (q) =>                        // recherche globale par nom
  apiFetch(`/equipements/search/?q=${encodeURIComponent(q)}`)

// Equipements de la zone visible : bounds = LatLngBounds Leaflet,
// filtres = codes domaines coches + ids de communes selectionnees
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

// ── Authentification ────────────────────────────────────────────
export const login = (username, password) =>
  apiFetch('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) })

export const register = (username, password) =>
  apiFetch('/auth/register/', { method: 'POST', body: JSON.stringify({ username, password }) })

export const logout = () => apiFetch('/auth/logout/', { method: 'POST' })

// ── Implantations (CRUD, requiert le token) ─────────────────────
export const fetchImplantations = () => apiFetch('/implantations/')

export const createImplantation = (data) =>
  apiFetch('/implantations/', { method: 'POST', body: JSON.stringify(data) })

export const updateImplantation = (id, data) =>
  apiFetch(`/implantations/${id}/`, { method: 'PUT', body: JSON.stringify(data) })

export const deleteImplantation = (id) => apiFetch(`/implantations/${id}/`, { method: 'DELETE' })
