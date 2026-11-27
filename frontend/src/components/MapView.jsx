import { useEffect, useRef, useState } from 'react'
import {
  GeoJSON,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from 'react-leaflet'
import L from 'leaflet'
import { fetchEquipements } from '../api'

// style des points BPE (petits cercles bleus via circleMarker,
// beaucoup plus performant que des icones pour des milliers de points)
const equipementStyle = {
  radius: 5,
  fillColor: '#000091',
  color: '#fff',
  weight: 1,
  fillOpacity: 0.85,
}

// icones custom en pur CSS (DivIcon) pour les autres marqueurs
const implantationIcon = new L.DivIcon({   // rouge : implantation enregistree
  className: 'imp-icon',
  html: '<div class="imp-dot"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})
const draftIcon = new L.DivIcon({          // vert : brouillon pas encore enregistre
  className: 'imp-icon',
  html: '<div class="imp-dot draft"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})
const searchIcon = new L.DivIcon({         // violet : adresse geocodee
  className: 'imp-icon',
  html: '<div class="imp-dot search"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})
const focusIcon = new L.DivIcon({          // orange : equipement trouve par la recherche
  className: 'imp-icon',
  html: '<div class="imp-dot focus"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

// contenu HTML des popups des equipements BPE
function popupHtml(p) {
  return `<b>${p.nom || p.domaine3_libelle}</b><br>
    ${p.adresse || ''} ${p.codepostal} ${p.ville}<br>
    <i>${p.domaine3_libelle}</i><br>
    SIRET : ${p.siret || '—'}`
}

// Envoie la bbox au parent quand la carte bouge + au montage.
// C'est la cle du chargement dynamique : on ne demande a l'API
// que les equipements de la zone visible.
function ViewportWatcher({ onChange }) {
  const map = useMapEvents({
    moveend: () => onChange(map.getBounds()),
  })
  useEffect(() => { onChange(map.getBounds()) }, [map, onChange])
  return null
}

// En mode "ajout", un clic sur la carte cree le brouillon d'implantation
function ClickHandler({ active, onDraft }) {
  useMapEvents({
    click: (e) => { if (active) onDraft(e.latlng) },
  })
  return null
}

// Anime la carte vers une cible [lng, lat] quand le parent en envoie une
function FlyTo({ target }) {
  const map = useMap()
  useEffect(() => {
    if (target) map.flyTo([target[1], target[0]], 15)
  }, [target, map])
  return null
}

export default function MapView({ filters, implantations, adding, draft, setDraft, searched, focusEquip, flyTo }) {
  const [bounds, setBounds] = useState(null)   // bbox actuellement affichee
  const [data, setData] = useState(null)       // FeatureCollection GeoJSON recue de l'API
  const [version, setVersion] = useState(0)    // compteur qui force le remontage de la couche GeoJSON
  const [count, setCount] = useState(0)        // nb total d'equipements dans la zone (statusbar)
  const [truncated, setTruncated] = useState(false)  // l'API a-t-elle tronque a 5000 ?
  const [loading, setLoading] = useState(false)
  const seq = useRef(0)   // numero de la derniere requete emise (anti-course)

  // Requete API des que la bbox ou les filtres changent.
  // Anti-course : si l'utilisateur bouge la carte pendant une requete,
  // la reponse obsolete (n ancien) est ignoree.
  useEffect(() => {
    if (!bounds) return
    const n = ++seq.current
    setLoading(true)
    fetchEquipements(bounds, filters)
      .then((d) => {
        if (n !== seq.current) return // reponse obsolete (la carte a rebouge)
        setData(d)
        setVersion((v) => v + 1)
        setCount(d.count)
        setTruncated(d.truncated)
      })
      .catch(console.error)
      .finally(() => n === seq.current && setLoading(false))
  }, [bounds, filters])

  return (
    <div className="map-wrap">
      <MapContainer center={[49.1, 0.4]} zoom={9} className="map">
        {/* fond de carte OpenStreetMap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ViewportWatcher onChange={setBounds} />
        <ClickHandler active={adding} onDraft={setDraft} />
        <FlyTo target={flyTo} />

        {/* couche des equipements BPE.
            key={version} : force React a remonter le composant a chaque
            nouvelle reponse, sinon Leaflet garderait les anciens points */}
        {data && (
          <GeoJSON
            key={version}
            data={data}
            pointToLayer={(_, latlng) => L.circleMarker(latlng, equipementStyle)}
            onEachFeature={(f, layer) => layer.bindPopup(popupHtml(f.properties))}
          />
        )}

        {/* implantations personnelles (rouge) */}
        {implantations.map((imp) => (
          <Marker
            key={imp.id}
            position={[imp.geometry.coordinates[1], imp.geometry.coordinates[0]]}
            icon={implantationIcon}
          >
            <Popup>
              <b>{imp.titre}</b>
              {imp.domaine3 && <><br /><i>Type : {imp.domaine3}</i></>}
              {imp.commentaire && <><br />{imp.commentaire}</>}
            </Popup>
          </Marker>
        ))}

        {/* brouillon en cours de placement (vert) */}
        {draft && (
          <Marker position={draft} icon={draftIcon}>
            <Popup>Nouvelle implantation</Popup>
          </Marker>
        )}

        {/* adresse geocodee (violet) */}
        {searched && (
          <Marker position={[searched.lat, searched.lng]} icon={searchIcon}>
            <Popup>{searched.label}</Popup>
          </Marker>
        )}

        {/* equipement trouve par la recherche (orange), popup ouverte d'office */}
        {focusEquip && (
          <Marker
            position={[focusEquip.lat, focusEquip.lon]}
            icon={focusIcon}
            eventHandlers={{ add: (e) => e.target.openPopup() }}
          >
            <Popup>
              <b>{focusEquip.nom || focusEquip.domaine3_libelle}</b>
              <br />
              {focusEquip.adresse} {focusEquip.codepostal} {focusEquip.ville}
              <br />
              <i>{focusEquip.domaine3_libelle}</i>
              <br />
              SIRET : {focusEquip.siret || '—'}
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* compteur d'equipements dans la zone affichee */}
      <div className="statusbar">
        <b>{loading ? 'Chargement…' : `${count} équipements`}</b> dans la zone affichée
        {truncated && ' — zoomez pour tout voir'}
      </div>

      <div className="legend">
        <div className="k"><span className="sw eq"></span>Équipement BPE</div>
        <div className="k"><span className="sw imp"></span>Implantation potentielle</div>
        <div className="k"><span className="sw adr"></span>Adresse recherchée</div>
      </div>
    </div>
  )
}
