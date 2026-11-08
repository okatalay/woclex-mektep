import { Megaphone } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, Empty, ErrorNote, PageHeader, PageLoader } from '../components/ui.jsx'

export default function Announcements() {
  const { data: announcements, loading, error } = useLoad(() => api.get('/me/announcements'), [])

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader title="Duyurular" subtitle="Eğitmenlerin sınıflara yaptığı duyurular." />
      <ErrorNote error={error} />
      {announcements?.length ? (
        <div className="stack">
          {announcements.map((a) => (
            <Card key={a.id}>
              <div className="row-between row">
                <strong>{a.classroom_name}</strong>
                <span className="muted">{new Date(a.created_at).toLocaleDateString('tr-TR')}</span>
              </div>
              <p>{a.body}</p>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={Megaphone} title="Henüz duyuru yok" text="Eğitmenin bir duyuru paylaştığında burada göreceksin." />
        </Card>
      )}
    </>
  )
}
