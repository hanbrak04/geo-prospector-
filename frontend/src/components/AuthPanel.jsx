import { useState } from 'react'
import { login, register } from '../api'

// Panneau de connexion/inscription (visible uniquement deconnecte).
// Le meme formulaire sert aux deux actions : login verifie le mot de passe,
// register cree le compte — les deux renvoient un token.
export default function AuthPanel({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  // action = login ou register (memes arguments, meme reponse {token, username})
  async function submit(action) {
    try {
      setError('')
      onLogin(await action(username, password))
    } catch (e) {
      setError(e.message)   // ex. "identifiants invalides"
    }
  }

  return (
    <div className="panel">
      <h2>Connexion</h2>
      <input placeholder="Identifiant" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Mot de passe" value={password} onChange={(e) => setPassword(e.target.value)} />
      <div className="row">
        <button onClick={() => submit(login)}>Connexion</button>
        <button className="secondary" onClick={() => submit(register)}>Créer un compte</button>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  )
}
