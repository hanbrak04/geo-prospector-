// Point d'entree React : monte le composant racine <App/> dans #root (index.html)
// StrictMode : detecte les effets de bord en dev (double-render volontaire)
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
