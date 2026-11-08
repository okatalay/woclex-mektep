import { Link } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, Empty, ErrorNote, PageHeader, PageLoader } from '../components/ui.jsx'

export default function MyRoutes() {
  const { data: routes, loading, error } = useLoad(() => api.get('/me/routes'), [])

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader title="Rotalarım" subtitle="Eğitmeninin tanımladığı yolculuklarda adım adım ilerle." />
      <ErrorNote error={error} />
      {routes?.length ? (
        <div className="grid grid-cards">
          {routes.map((r) => (
            <Card as={Link} to={`/panel/rotalarim/${r.id}`} className="stack" key={r.id}>
              <h3>{r.title}</h3>
              <div className="progress-bar"><div className="progress-bar-fill" style={{ width: `${r.progress_pct}%` }} /></div>
              <span className="muted">{r.completed_count}/{r.stop_count} durak tamamlandı</span>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={MapPin} title="Henüz rotan yok" text="Eğitmenin bir rota tanımladığında burada göreceksin." />
        </Card>
      )}
    </>
  )
}
