import { useRef, useState } from 'react'
import { fetchAdresses, fetchCommunes, fetchEquipementsByNom } from '../api'

const EMPTY = { villes: [], adresses: [], equipements: [] }

export default function SearchPanel({
  onSelectVille,
  onSelectAdresse,
  onSelectEquipement,
  onImplanter,
  searched,
  logged,
}) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(EMPTY)
  const [searching, setSearching] = useState(false)
  const seq = useRef(0)

  async function search(q) {
    setQuery(q)
    if (q.length < 2) return setResults(EMPTY)
    const n = ++seq.current
    setSearching(true)
    try {
      const [villes, adresses, equipements] = await Promise.all([
        fetchCommunes(q),
        fetchAdresses(q),
        fetchEquipementsByNom(q),
      ])
      if (n !== seq.current) return // reponse obsolete
      setResults({
        villes: villes.slice(0, 5),
        adresses: adresses.slice(0, 5),
        equipements: equipements.slice(0, 8),
      })
    } catch {
      setResults(EMPTY)
    } finally {
      if (n === seq.current) setSearching(false)
    }
  }

  function pickVille(c) {
    onSelectVille(c)
    reset(`Ville : ${c.nom}`)
  }

  function pickAdresse(a) {
    onSelectAdresse({ lat: a.lat, lng: a.lon, label: a.label })
    reset(a.label)
  }

  function pickEquipement(e) {
    onSelectEquipement(e)
    reset(e.nom || e.domaine3_libelle)
  }

  function reset(value) {
    setResults(EMPTY)
    setQuery(value)
  }

  const hasResults =
    results.villes.length + results.adresses.length + results.equipements.length > 0

  return (
    <div className="panel">
      <h2>Recherche</h2>
      <input
        placeholder="ville, adresse ou équipement…"
        value={query}
        onChange={(e) => search(e.target.value)}
      />
      {hasResults && (
        <ul className="dropdown">
          {results.villes.length > 0 && <li className="group">🏙 Villes</li>}
          {results.villes.map((c) => (
            <li key={`v${c.id}`} onClick={() => pickVille(c)}>
              {c.nom} <span className="muted">({c.dept})</span>
            </li>
          ))}
          {results.adresses.length > 0 && <li className="group">📍 Adresses</li>}
          {results.adresses.map((a, i) => (
            <li key={`a${i}`} onClick={() => pickAdresse(a)}>{a.label}</li>
          ))}
          {results.equipements.length > 0 && <li className="group">🏪 Équipements</li>}
          {results.equipements.map((e) => (
            <li key={`e${e.id}`} onClick={() => pickEquipement(e)}>
              {e.nom || e.domaine3_libelle}
              <span className="muted"> — {e.ville}</span>
            </li>
          ))}
        </ul>
      )}
      {query.length >= 2 && !hasResults && !searching && (
        <p className="hint">Aucun résultat.</p>
      )}
      {searched && (
        <div>
          <p className="hint">📍 {searched.label}</p>
          {searched.horsZone && (
            <p className="error">
              ⚠️ Cette adresse est en dehors de la zone d'étude (Normandie).
            </p>
          )}
          <div className="row">
            {logged && !searched.horsZone && (
              <button onClick={() => onImplanter(searched)}>Implanter ici</button>
            )}
            <button className="secondary" onClick={() => onSelectAdresse(null)}>
              Effacer
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
