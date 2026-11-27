import { useState } from 'react'
import { createImplantation, updateImplantation, deleteImplantation } from '../api'

function Domaine3Select({ domaines, value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">— type de commerce (BPE) —</option>
      {domaines.map((d1) => (
        <optgroup key={d1.code} label={d1.libelle}>
          {d1.enfants.map((d2) =>
            d2.enfants.map((d3) => (
              <option key={d3.code} value={d3.code}>{d3.libelle}</option>
            ))
          )}
        </optgroup>
      ))}
    </select>
  )
}

export default function ImplantationPanel({
  logged, domaines, implantations, adding, setAdding, draft, setDraft, onRefresh, onFlyTo,
}) {
  const [titre, setTitre] = useState('')
  const [commentaire, setCommentaire] = useState('')
  const [domaine3, setDomaine3] = useState('')
  const [editing, setEditing] = useState(null)

  if (!logged) {
    return (
      <div className="panel">
        <h2>Implantations potentielles</h2>
        <p>Connectez-vous pour ajouter vos propres points.</p>
      </div>
    )
  }

  function resetForm() {
    setTitre(''); setCommentaire(''); setDomaine3(''); setEditing(null); setDraft(null)
  }

  async function save() {
    const payload = { titre, commentaire, domaine3: domaine3 || null }
    if (editing) {
      await updateImplantation(editing.id, { ...payload, lon: editing.geom.x, lat: editing.geom.y })
    } else {
      await createImplantation({ ...payload, lon: draft.lng, lat: draft.lat })
    }
    resetForm(); setAdding(false); onRefresh()
  }

  function startEdit(imp) {
    setEditing({ ...imp, geom: { x: imp.geometry.coordinates[0], y: imp.geometry.coordinates[1] } })
    setTitre(imp.titre)
    setCommentaire(imp.commentaire)
    setDomaine3(imp.domaine3 || '')
    setDraft(null); setAdding(false)
  }

  async function remove(id) {
    if (window.confirm('Supprimer cette implantation ?')) {
      await deleteImplantation(id)
      onRefresh()
    }
  }

  return (
    <div className="panel">
      <h2>Implantations potentielles</h2>

      {adding && <p className="hint">Cliquez sur la carte pour placer votre point…</p>}
      {draft && !editing && (
        <div className="form">
          <p className="hint">Point : {draft.lat.toFixed(5)}, {draft.lng.toFixed(5)}</p>
          <input placeholder="Titre" value={titre} onChange={(e) => setTitre(e.target.value)} />
          <Domaine3Select domaines={domaines} value={domaine3} onChange={setDomaine3} />
          <textarea placeholder="Commentaires…" value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
          <div className="row">
            <button onClick={save} disabled={!titre}>Enregistrer</button>
            <button className="secondary" onClick={() => { resetForm(); setAdding(false) }}>Annuler</button>
          </div>
        </div>
      )}
      {editing && (
        <div className="form">
          <p className="hint">Modifier « {editing.titre} »</p>
          <input placeholder="Titre" value={titre} onChange={(e) => setTitre(e.target.value)} />
          <Domaine3Select domaines={domaines} value={domaine3} onChange={setDomaine3} />
          <textarea placeholder="Commentaires…" value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
          <div className="row">
            <button onClick={save} disabled={!titre}>Enregistrer</button>
            <button className="secondary" onClick={resetForm}>Annuler</button>
          </div>
        </div>
      )}

      {!adding && !draft && !editing && (
        <button onClick={() => setAdding(true)}>+ Ajouter une implantation</button>
      )}

      <ul className="list">
        {implantations.map((imp) => (
          <li key={imp.id}>
            <span className="link" onClick={() => onFlyTo(imp.geometry.coordinates)}>
              {imp.titre}
            </span>
            <span className="actions">
              <button onClick={() => startEdit(imp)}>✎</button>
              <button onClick={() => remove(imp.id)}>✕</button>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
