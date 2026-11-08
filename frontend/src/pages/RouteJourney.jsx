import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, Check, Lock } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, ErrorNote, PageHeader, PageLoader } from '../components/ui.jsx'

function stopState(s) {
  if (s.status === 'incelendi') return 'done'
  if (s.locked) return 'locked'
  return 'current'
}

const STATE_LABEL = {
  done: 'Tamamlandı',
  current: 'Sırada',
  locked: 'Kilitli',
}

export default function RouteJourney() {
  const { routeId } = useParams()
  const { data: route, loading, error } = useLoad(() => api.get(`/me/routes/${routeId}`), [routeId])

  if (loading) return <PageLoader />
  if (error || !route) return <ErrorNote error={error} />

  const currentIndex = route.stops.findIndex((s) => stopState(s) === 'current')
  const heroText = route.completed_count === 0
    ? 'İlk durak seni bekliyor'
    : route.completed_count === route.stop_count
      ? 'Yolculuğunu tamamladın 🎉'
      : `${currentIndex + 1}. durağa geldin`

  return (
    <>
      <Link to="/panel/rotalarim" className="back"><ChevronLeft size={16} aria-hidden="true" />Rotalarım</Link>

      <Card className="journey-hero">
        <span className="journey-eyebrow">Yolculuğun</span>
        <h1 className="journey-title">{route.title}</h1>
        {route.description && <p className="muted">{route.description}</p>}
        <p className="journey-status">{heroText}</p>
        <div className="progress-bar" style={{ marginTop: 10 }}>
          <div className="progress-bar-fill" style={{ width: `${route.progress_pct}%` }} />
        </div>
        <span className="muted journey-count">{route.completed_count}/{route.stop_count} durak tamamlandı</span>
      </Card>

      <div className="route-timeline">
        {route.stops.map((s, i) => {
          const state = stopState(s)
          return (
            <div className={`route-node route-node-${state}`} key={s.stop_id}>
              <div className="route-node-rail">
                <span className="route-node-dot">
                  {state === 'done' ? <Check size={16} /> : state === 'locked' ? <Lock size={14} /> : i + 1}
                </span>
                {i < route.stops.length - 1 && <span className="route-node-line" />}
              </div>
              <Card className="route-node-card">
                <div className="row-between row">
                  <strong>{s.title}</strong>
                  <span className={`route-state-label route-state-${state}`}>{STATE_LABEL[state]}</span>
                </div>
                {state === 'locked' ? (
                  <p className="muted" style={{ margin: '4px 0 0' }}>Önceki adımı tamamlayın</p>
                ) : (
                  <Link
                    to={`/panel/odevlerim/${s.assignment_id}`}
                    className={`btn btn-${state === 'done' ? 'secondary' : 'primary'} route-node-cta`}
                  >
                    {state === 'done' ? 'Teslimini gör' : s.status === 'tekrar_istendi' ? 'Tekrar teslim et →' : i === 0 && route.completed_count === 0 ? 'Başla →' : 'Göreve git →'}
                  </Link>
                )}
              </Card>
            </div>
          )
        })}
      </div>
    </>
  )
}
