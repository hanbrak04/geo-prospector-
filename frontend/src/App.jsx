import { useCallback, useEffect, useState } from 'react'
import 'leaflet/dist/leaflet.css'
import './App.css'
import { fetchDomaines, fetchAdresses, getToken, fetchImplantations, logout } from './api'
import AuthPanel from './components/AuthPanel'
import SearchPanel from './components/SearchPanel'
import FilterPanel from './components/FilterPanel'
import ImplantationPanel from './components/ImplantationPanel'
import MapView from './components/MapView'

// etat initial des filtres : rien de coche
const EMPTY_FILTERS = { d1: [], d2: [], d3: [], communes: [] }

// bbox de la Normandie (minLon, minLat, maxLon, maxLat) :
// sert a detecter si une adresse geocodee est hors de la zone d'etude
const ZONE_BBOX = [-2.0, 48.1, 1.9, 50.1]

function inZone(lng, lat) {
  const [w, s, e, n] = ZONE_BBOX
  return lng >= w && lng <= e && lat >= s && lat <= n
}

function App() {
  // ── Etat global de l'application ──
  const [logged, setLogged] = useState(!!getToken())          // token present = deja connecte
  const [user, setUser] = useState(localStorage.getItem('username') || '')
  const [domaines, setDomaines] = useState([])                // arbre des domaines BPE (niveaux 1-3)
  const [filters, setFilters] = useState(EMPTY_FILTERS)       // filtres actifs (codes domaines + ids communes)
  const [communeObjs, setCommuneObjs] = useState([])          // communes selectionnees (objets complets, pour les chips)
  const [implantations, setImplantations] = useState([])      // points personnels de l'utilisateur
  const [adding, setAdding] = useState(false)                 // mode "cliquer pour placer un point"
  const [draft, setDraft] = useState(null)                    // point pose, formulaire pas encore valide
  const [flyTo, setFlyTo] = useState(null)                    // [lng, lat] vers lequel la carte doit voler
  const [searched, setSearched] = useState(null)              // adresse geocodee affichee (marqueur violet)
  const [focusEquip, setFocusEquip] = useState(null)          // equipement trouve par recherche (marqueur orange)

  // charge l'arbre des domaines une seule fois au demarrage
  useEffect(() => {
    fetchDomaines().then(setDomaines).catch(console.error)
  }, [])

  // recharge les implantations (sert apres login/logout et apres chaque CRUD)
  const refreshImplantations = useCallback(() => {
    if (getToken()) fetchImplantations().then(setImplantations).catch(console.error)
    else setImplantations([])
  }, [])

  useEffect(refreshImplantations, [logged, refreshImplantations])

  // ── Authentification ──
  function onLogin(data) {
    localStorage.setItem('token', data.token)       // le token persiste entre les sessions
    localStorage.setItem('username', data.username)
    setUser(data.username)
    setLogged(true)
  }

  async function signOut() {
    try { await logout() } catch { /* token deja invalide cote serveur */ }
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setLogged(false)
  }

  // ── Callbacks de la barre de recherche unifiee ──

  // clic sur une adresse geocodee : marqueur violet + vol de la carte
  // + detection hors zone pour afficher l'avertissement
  function selectAdresse(a) {
    if (a) a = { ...a, horsZone: !inZone(a.lng, a.lat) }
    setSearched(a)
    if (a) setFlyTo([a.lng, a.lat])
  }

  // "Implanter ici" : transforme l'adresse geocodee en brouillon d'implantation
  function implanterIci(a) {
    setDraft({ lat: a.lat, lng: a.lng })
    setAdding(true)
  }

  // clic sur un equipement de la recherche : marqueur orange + fiche ouverte
  function selectEquipement(e) {
    setFocusEquip(e)
    if (e) setFlyTo([e.lon, e.lat])
  }

  // met a jour les communes selectionnees : les chips (objets)
  // ET les filtres envoyes a l'API (ids)
  function applyCommunes(next) {
    setCommuneObjs(next)
    setFilters((f) => ({ ...f, communes: next.map((c) => c.id) }))
  }

  // clic sur une ville : ajout en chip de filtre (sans doublon)
  // + centrage de la carte sur la mairie via le geocodage BAN
  async function selectVille(c) {
    if (!communeObjs.some((x) => x.id === c.id)) {
      applyCommunes([...communeObjs, c])
    }
    // type=municipality -> on recupere le centre de la commune (la mairie)
    const res = await fetchAdresses(c.nom, 'municipality')
    if (res.length) setFlyTo([res[0].lon, res[0].lat])
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS)
    setCommuneObjs([])
  }

  return (
    <div>
      {/* ── Bandeau superieur style Etat ── */}
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
        {/* ── Barre laterale : connexion, recherche, filtres, implantations ── */}
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

        {/* ── Carte Leaflet ── */}
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
