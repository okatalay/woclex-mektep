import { Link } from 'react-router-dom'
import { BookOpen, ChevronRight } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, Empty, ErrorNote, PageHeader, PageLoader, Pill } from '../components/ui.jsx'

const STATUS_LABEL = {
  bekliyor: 'Bekliyor',
  teslim_edildi: 'Teslim edildi',
  incelendi: 'İncelendi',
  tekrar_istendi: 'Tekrar teslim et',
}
const STATUS_TONE = {
  bekliyor: 'neutral',
  teslim_edildi: 'accent',
  incelendi: 'ok',
  tekrar_istendi: 'warn',
}

export default function MyAssignments() {
  const { data: assignments, loading, error } = useLoad(() => api.get('/me/assignments'), [])

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader title="Ödevlerim" subtitle="Eğitmeninin sana atadığı ödevler." />
      <ErrorNote error={error} />
      <Card>
        {assignments?.length ? (
          <div className="list">
            {assignments.map((a) => (
              <Link className="list-item" to={`/panel/odevlerim/${a.id}`} key={a.id}>
                <div className="grow">
                  <strong>{a.title}</strong>
                  {a.due_at && <div className="muted">Son tarih: {new Date(a.due_at).toLocaleDateString('tr-TR')}</div>}
                </div>
                <Pill tone={STATUS_TONE[a.submission.status]}>{STATUS_LABEL[a.submission.status]}</Pill>
                <ChevronRight size={18} aria-hidden="true" className="muted" />
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={BookOpen} title="Henüz ödev yok" text="Eğitmenin ödev atadığında burada göreceksin." />
        )}
      </Card>
    </>
  )
}
