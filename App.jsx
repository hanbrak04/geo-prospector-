import { useCallback, useEffect, useState } from 'react'
import 'leaflet/dist/leaflet.css'
import './App.css'
import { fetchDomaines, getToken, fetchImplantations } from './api'
import AuthPanel from './components/AuthPanel'
import FilterPanel from './components/FilterPanel'
import ImplantationPanel from './components/ImplantationPanel'
import MapView from './components/MapView'

const EMPTY_FILTERS = { d1: [], d2: [], d3: [], communes: [] }

function App() {
  const [logged, setLogged] = useState(!!getToken())
  const [domaines, setDomaines] = useState([])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [implantations, setImplantations] = useState([])
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState(null)
  const [flyTo, setFlyTo] = useState(null)

  useEffect(() => {
    fetchDomaines().then(setDomaines).catch(console.error)
  }, [])

  const refreshImplantations = useCallback(() => {
    if (getToken()) fetchImplantations().then(setImplantations).catch(console.error)
    else setImplantations([])
  }, [])

  useEffect(refreshImplantations, [logged, refreshImplantations])

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Geo Prospector</h1>
        <p className="subtitle">Normandie — équipements BPE 2025</p>
        <AuthPanel logged={logged} onChange={setLogged} />
        <FilterPanel domaines={domaines} filters={filters} onChange={setFilters} />
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
        flyTo={flyTo}
      />
    </div>
  )
}

export default App
