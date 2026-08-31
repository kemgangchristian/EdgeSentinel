import { useEffect, useMemo, useState, useCallback } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const relativeFormatter = new Intl.RelativeTimeFormat('fr', { numeric: 'auto' })

function relativeTime(isoString) {
  const diffMs = new Date(isoString).getTime() - Date.now()
  const diffMin = Math.round(diffMs / 60000)
  if (Math.abs(diffMin) < 1) return "à l'instant"
  if (Math.abs(diffMin) < 60) return relativeFormatter.format(diffMin, 'minute')
  const diffHours = Math.round(diffMin / 60)
  if (Math.abs(diffHours) < 24) return relativeFormatter.format(diffHours, 'hour')
  const diffDays = Math.round(diffHours / 24)
  return relativeFormatter.format(diffDays, 'day')
}

function eventLabel(event) {
  if (event.eventType === 'INTRUSION') {
    return event.zone ? `Intrusion détectée en ${event.zone}` : 'Intrusion détectée'
  }
  return 'Personne détectée'
}

function EventRow({ event, isLatest }) {
  const isIntrusion = event.eventType === 'INTRUSION'
  const confidencePct = Math.round(event.confidence * 100)

  return (
    <li className={`event-row ${isIntrusion ? 'event-row--intrusion' : 'event-row--detected'}`}>
      <div className="event-row__main">
        {isLatest && <span className="event-row__pulse" aria-hidden="true" />}
        <span className="event-row__label">{eventLabel(event)}</span>
        <span className="event-row__device">{event.deviceId}</span>
      </div>
      <div className="event-row__meta">
        <time className="event-row__time" dateTime={event.timestamp} title={event.timestamp}>
          {relativeTime(event.timestamp)}
        </time>
        <span className="event-row__confidence">{confidencePct}%</span>
      </div>
    </li>
  )
}

function App() {
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState('loading') // loading | ready | error
  const [errorMessage, setErrorMessage] = useState('')

  const loadEvents = useCallback(() => {
    setStatus('loading')
    fetch(`${API_BASE_URL}/api/events`)
      .then((response) => {
        if (!response.ok) throw new Error(`Erreur HTTP ${response.status}`)
        return response.json()
      })
      .then((data) => {
        setEvents(data.content)
        setStatus('ready')
      })
      .catch((err) => {
        setErrorMessage(err.message)
        setStatus('error')
      })
  }, [])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  const { intrusionCount, detectionCount } = useMemo(() => {
    return events.reduce(
      (acc, event) => {
        if (event.eventType === 'INTRUSION') acc.intrusionCount += 1
        else acc.detectionCount += 1
        return acc
      },
      { intrusionCount: 0, detectionCount: 0 }
    )
  }, [events])

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__identity">
          <h1 className="app-header__wordmark">EdgeSentinel</h1>
          <p className="app-header__tagline">Surveillance caméra Edge</p>
        </div>
        <button className="refresh-button" onClick={loadEvents} disabled={status === 'loading'}>
          {status === 'loading' ? 'Actualisation…' : 'Actualiser'}
        </button>
      </header>

      {status === 'ready' && events.length > 0 && (
        <div className="stats-row">
          <span className="stat stat--intrusion">
            <span className="stat__dot" aria-hidden="true" />
            {intrusionCount} intrusion{intrusionCount !== 1 ? 's' : ''}
          </span>
          <span className="stat stat--detected">
            <span className="stat__dot" aria-hidden="true" />
            {detectionCount} détection{detectionCount !== 1 ? 's' : ''}
          </span>
          <span className="stats-row__scope">sur les {events.length} derniers événements</span>
        </div>
      )}

      <main className="app-main" aria-live="polite">
        {status === 'loading' && events.length === 0 && (
          <p className="state-message">Chargement de l'activité récente…</p>
        )}

        {status === 'error' && (
          <p className="state-message state-message--error">
            Impossible de joindre le backend. Vérifiez qu'il tourne sur {API_BASE_URL}.
          </p>
        )}

        {status === 'ready' && events.length === 0 && (
          <p className="state-message">
            Aucun événement pour l'instant. Démarrez l'agent Edge pour commencer la surveillance.
          </p>
        )}

        {events.length > 0 && (
          <ul className="event-feed">
            {events.map((event, index) => (
              <EventRow key={event.id} event={event} isLatest={index === 0} />
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}

export default App