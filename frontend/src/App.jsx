import { useCallback, useEffect, useState } from 'react'
import 'leaflet/dist/leaflet.css'
import './App.css'
import { fetchDomaines, fetchAdresses, getToken, fetchImplantations, logout } from './api'
import AuthPanel from './components/AuthPanel'
import SearchPanel from './components/SearchPanel'
import FilterPanel from './components/FilterPanel'
import ImplantationPanel from './components/ImplantationPanel'
import MapView from './components/MapView'

const EMPTY_FILTERS = { d1: [], d2: [], d3: [], communes: [] }

// bbox de la Normandie (minLon, minLat, maxLon, maxLat)
const ZONE_BBOX = [-2.0, 48.1, 1.9, 50.1]

function inZone(lng, lat) {
  const [w, s, e, n] = ZONE_BBOX
  return lng >= w && lng <= e && lat >= s && lat <= n
}

function App() {
  const [logged, setLogged] = useState(!!getToken())
  const [user, setUser] = useState(localStorage.getItem('username') || '')
  const [domaines, setDomaines] = useState([])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [communeObjs, setCommuneObjs] = useState([])
  const [implantations, setImplantations] = useState([])
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState(null)
  const [flyTo, setFlyTo] = useState(null)
  const [searched, setSearched] = useState(null)
  const [focusEquip, setFocusEquip] = useState(null)

  useEffect(() => {
    fetchDomaines().then(setDomaines).catch(console.error)
  }, [])

  const refreshImplantations = useCallback(() => {
    if (getToken()) fetchImplantations().then(setImplantations).catch(console.error)
    else setImplantations([])
  }, [])

  useEffect(refreshImplantations, [logged, refreshImplantations])

  function onLogin(data) {
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.username)
    setUser(data.username)
    setLogged(true)
  }

  async function signOut() {
    try { await logout() } catch { /* token deja invalide */ }
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setLogged(false)
  }

  function selectAdresse(a) {
    if (a) a = { ...a, horsZone: !inZone(a.lng, a.lat) }
    setSearched(a)
    if (a) setFlyTo([a.lng, a.lat])
  }

  function implanterIci(a) {
    setDraft({ lat: a.lat, lng: a.lng })
    setAdding(true)
  }

  function selectEquipement(e) {
    setFocusEquip(e)
    if (e) setFlyTo([e.lon, e.lat])
  }

  function applyCommunes(next) {
    setCommuneObjs(next)
    setFilters((f) => ({ ...f, communes: next.map((c) => c.id) }))
  }

  async function selectVille(c) {
    if (!communeObjs.some((x) => x.id === c.id)) {
      applyCommunes([...communeObjs, c])
    }
    // centre la carte sur la mairie de la commune
    const res = await fetchAdresses(c.nom, 'municipality')
    if (res.length) setFlyTo([res[0].lon, res[0].lat])
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS)
    setCommuneObjs([])
  }

  return (
    <div>
      <header className="top">
        <div>
          <div className="marianne">République · Données BPE / INSEE</div>
          <h1>Geo Prospector</h1>
        </div>
        <div className="region-tag">Normandie — BPE 2025</div>
        <div className="spacer" />
        {logged ? (
          <div className="user-zone">
            <span>{user}</span>
            <button className="btn-header" onClick={signOut}>Déconnexion</button>
          </div>
        ) : (
          <span className="user-zone">Non connecté</span>
        )}
      </header>
      <div className="layout">
        <aside className="sidebar">
          {!logged && <AuthPanel onLogin={onLogin} />}
          <SearchPanel
            logged={logged}
            searched={searched}
            onSelectVille={selectVille}
            onSelectAdresse={selectAdresse}
            onSelectEquipement={selectEquipement}
            onImplanter={implanterIci}
          />
          <FilterPanel
            domaines={domaines}
            filters={filters}
            onChange={setFilters}
            communeObjs={communeObjs}
            onRemoveCommune={(c) => applyCommunes(communeObjs.filter((x) => x.id !== c.id))}
            onReset={resetFilters}
          />
          <ImplantationPanel
            logged={logged}
            domaines={domaines}
            implantations={implantations}
            adding={adding}
            setAdding={setAdding}
            draft={draft}
            setDraft={setDraft}
            onRefresh={refreshImplantations}
            onFlyTo={setFlyTo}
          />
        </aside>
        <MapView
          filters={filters}
          implantations={implantations}
          adding={adding}
          draft={draft}
          setDraft={setDraft}
          searched={searched}
          focusEquip={focusEquip}
          flyTo={flyTo}
        />
      </div>
    </div>
  )
}

export default App
