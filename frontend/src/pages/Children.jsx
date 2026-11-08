import { Link } from 'react-router-dom'
import { ChevronRight, Users } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, Empty, ErrorNote, PageHeader, PageLoader } from '../components/ui.jsx'
import ProgressStats from '../components/ProgressStats.jsx'

export default function Children() {
  const { data: children, loading, error } = useLoad(() => api.get('/guardians/me/children'), [])

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader title="Çocuklarım" subtitle="Bağlı olduğun öğrencileri ve ilerlemelerini gör." />
      <ErrorNote error={error} />
      {children?.length ? (
        <div className="stack">
          {children.map((c) => (
            <Card className="stack" key={c.student_id}>
              <Link to={`/panel/cocuklarim/${c.student_id}`} className="row-between row" style={{ color: 'var(--ink)' }}>
                <div>
                  <h3>{c.full_name}</h3>
                  {c.relation && <span className="pill pill-plain">{c.relation}</span>}
                </div>
                <ChevronRight size={18} aria-hidden="true" className="muted" />
              </Link>
              {c.classrooms.map((cl) => (
                <div className="muted" key={cl.id}>{cl.name} — {cl.teacher_name}</div>
              ))}
              <ProgressStats progress={c.progress} />
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={Users} title="Henüz bağlı bir çocuğun yok" text="Eğitmenin sana bir veli davet linki göndermeli." />
        </Card>
      )}
    </>
  )
}
