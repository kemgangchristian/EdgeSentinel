import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

function App() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/events`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Erreur HTTP ${response.status}`)
        }
        return response.json()
      })
      .then((data) => {
        setEvents(data.content)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Chargement des événements...</p>
  if (error) return <p>Erreur : {error}</p>

  return (
    <div>
      <h1>EdgeSentinel — Événements récents</h1>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            {event.timestamp} — {event.deviceId} — {event.eventType}
            {event.zone && ` (${event.zone})`}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App