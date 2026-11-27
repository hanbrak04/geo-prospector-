import { useState } from 'react'

function toggle(list, code) {
  return list.includes(code) ? list.filter((c) => c !== code) : [...list, code]
}

export default function FilterPanel({ domaines, filters, onChange, communeObjs, onRemoveCommune, onReset }) {
  const [open, setOpen] = useState({})

  function setLevel(level, code) {
    onChange({ ...filters, [level]: toggle(filters[level], code) })
  }

  return (
    <div className="panel">
      <h2>Filtres</h2>

      {communeObjs.length > 0 && (
        <div>
          <h3>Villes</h3>
          <div className="chips">
            {communeObjs.map((c) => (
              <span key={c.id} className="chip" onClick={() => onRemoveCommune(c)}>
                {c.nom} ✕
              </span>
            ))}
          </div>
        </div>
      )}

      <h3>Domaines</h3>
      <div className="tree">
        {domaines.map((d1) => (
          <div key={d1.code}>
            <label>
              <input type="checkbox" checked={filters.d1.includes(d1.code)} onChange={() => setLevel('d1', d1.code)} />
              <b>{d1.libelle}</b>
            </label>
            <button className="toggle" onClick={() => setOpen({ ...open, [d1.code]: !open[d1.code] })}>
              {open[d1.code] ? '−' : '+'}
            </button>
            {open[d1.code] && d1.enfants.map((d2) => (
              <div key={d2.code} className="lvl2">
                <label>
                  <input type="checkbox" checked={filters.d2.includes(d2.code)} onChange={() => setLevel('d2', d2.code)} />
                  {d2.libelle}
                </label>
                <button className="toggle" onClick={() => setOpen({ ...open, [d2.code]: !open[d2.code] })}>
                  {open[d2.code] ? '−' : '+'}
                </button>
                {open[d2.code] && d2.enfants.map((d3) => (
                  <div key={d3.code} className="lvl3">
                    <label>
                      <input type="checkbox" checked={filters.d3.includes(d3.code)} onChange={() => setLevel('d3', d3.code)} />
                      {d3.libelle}
                    </label>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}
      </div>
      <button className="secondary" onClick={onReset}>
        Réinitialiser les filtres
      </button>
    </div>
  )
}
