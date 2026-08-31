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

// "ZONE_A" -> "Zone A" : l'identifiant technique de config.yaml n'est pas
// ce qu'un utilisateur doit lire tel quel.
function formatZone(zone) {
  return zone
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// "captures/PI-001_....jpg" -> "PI-001_....jpg" : le champ stocké en base
// garde le chemin relatif complet (utile pour l'agent Edge), mais notre
// route HTTP /captures/** ne veut que le nom de fichier.
function captureUrl(capturePath) {
  if (!capturePath) return null
  const filename = capturePath.split('/').pop()
  return `${API_BASE_URL}/captures/${filename}`
}

function eventLabel(event) {
  if (event.eventType === 'INTRUSION') {
    return event.zone ? `Intrusion détectée en ${formatZone(event.zone)}` : 'Intrusion détectée'
  }
  return 'Personne détectée'
}

function EventRow({ event, isLatest, showDevice }) {
  const isIntrusion = event.eventType === 'INTRUSION'
  const confidencePct = Math.round(event.confidence * 100)
  const thumbnailUrl = captureUrl(event.capturePath)

  return (
    <li className={`event-row ${isIntrusion ? 'event-row--intrusion' : 'event-row--detected'}`}>
      {thumbnailUrl && (
        <img
          className="event-row__thumbnail"
          src={thumbnailUrl}
          alt={eventLabel(event)}
          loading="lazy"
        />
      )}
      <div className="event-row__main">
        {isLatest && <span className="event-row__pulse" aria-hidden="true" />}
        <span className="event-row__label">{eventLabel(event)}</span>
        {showDevice && <span className="event-row__device">{event.deviceId}</span>}
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
  // 'loading' est déjà l'état initial par défaut -- inutile de le
  // re-déclencher au montage, ce qui évite tout appel setState avant le
  // premier "await" dans l'effet de chargement initial (voir loadEvents).
  const [status, setStatus] = useState('loading') // loading | ready | error
  const [errorMessage, setErrorMessage] = useState('')

  // Aucun setState avant le premier "await" : la règle ESLint
  // react-hooks/set-state-in-effect interdit tout appel setState dans le
  // corps SYNCHRONE d'un effet -- y compris via une fonction async
  // invoquée directement, tant qu'il précède le premier "await".
  const loadEvents = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/events`)
      if (!response.ok) throw new Error(`Erreur HTTP ${response.status}`)
      const data = await response.json()
      setEvents(data.content)
      setStatus('ready')
    } catch (err) {
      setErrorMessage(err.message)
      setStatus('error')
    }
  }, [])

  // Le clic sur "Actualiser" n'est PAS un effet -- la règle ne s'y
  // applique pas, on peut y déclencher setStatus('loading') librement
  // pour donner un retour visuel immédiat.
  const handleRefresh = useCallback(() => {
    setStatus('loading')
    void loadEvents()
  }, [loadEvents])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadEvents()
  }, [loadEvents])

  const { intrusionCount, detectionCount, showDevice } = useMemo(() => {
    const uniqueDevices = new Set(events.map((event) => event.deviceId))
    return events.reduce(
      (acc, event) => {
        if (event.eventType === 'INTRUSION') acc.intrusionCount += 1
        else acc.detectionCount += 1
        return acc
      },
      { intrusionCount: 0, detectionCount: 0, showDevice: uniqueDevices.size > 1 }
    )
  }, [events])

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__identity">
          <h1 className="app-header__wordmark">EdgeSentinel</h1>
          <p className="app-header__tagline">Surveillance caméra Edge</p>
        </div>
        <button className="refresh-button" onClick={handleRefresh} disabled={status === 'loading'}>
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
            Impossible de joindre le backend ({errorMessage}). Vérifiez qu'il tourne sur {API_BASE_URL}.
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
              <EventRow key={event.id} event={event} isLatest={index === 0} showDevice={showDevice} />
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}

export default App