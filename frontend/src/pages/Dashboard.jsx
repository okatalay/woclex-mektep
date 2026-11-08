import { Link } from 'react-router-dom'
import { CheckCircle2, ClipboardCheck, GraduationCap, MessageCircle, Users } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../components/auth.jsx'
import { useLoad } from '../components/hooks'
import { Card, Empty, PageHeader, PageLoader, Pill } from '../components/ui.jsx'
import ProgressStats from '../components/ProgressStats.jsx'

function TeacherDashboard({ data }) {
  return (
    <>
      <div className="grid grid-3">
        <Card className="stat-card">
          <GraduationCap size={20} aria-hidden="true" className="stat-card-icon" />
          <span className="stat-value">{data.classes_count}</span>
          <span className="stat-label">Sınıf</span>
        </Card>
        <Card className="stat-card">
          <Users size={20} aria-hidden="true" className="stat-card-icon" />
          <span className="stat-value">{data.students_count}</span>
          <span className="stat-label">Öğrenci</span>
        </Card>
        <Card className="stat-card">
          <ClipboardCheck size={20} aria-hidden="true" className="stat-card-icon" />
          <span className="stat-value">{data.pending_review_count}</span>
          <span className="stat-label">İncelenecek teslim</span>
        </Card>
      </div>
      <Card>
        <h3>İncelenecek teslimler</h3>
        {data.recent_pending.length ? (
          <div className="list">
            {data.recent_pending.map((p) => (
              <Link className="list-item" to={`/panel/siniflar/${p.classroom_id}/odevler/${p.assignment_id}`} key={p.submission_id}>
                <div className="grow">
                  <strong>{p.student_name}</strong>
                  <div className="muted">{p.assignment_title}</div>
                </div>
                <Pill tone="accent">İncelenecek</Pill>
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={CheckCircle2} title="İncelenecek teslim yok" text="Tüm teslimler güncel." />
        )}
      </Card>
    </>
  )
}

function StudentDashboard({ data }) {
  return (
    <>
      <Card>
        <h3>İlerleme</h3>
        <ProgressStats progress={data.progress} />
      </Card>
      <Card>
        <div className="row-between row">
          <h3>Bekleyen ödevler</h3>
          <Link to="/panel/odevlerim" className="muted">Tümünü gör</Link>
        </div>
        {data.pending_assignments.length ? (
          <div className="list">
            {data.pending_assignments.map((a) => (
              <Link className="list-item" to={`/panel/odevlerim/${a.id}`} key={a.id}>
                <div className="grow">
                  <strong>{a.title}</strong>
                  {a.due_at && <div className="muted">Son tarih: {new Date(a.due_at).toLocaleDateString('tr-TR')}</div>}
                </div>
                <Pill tone={a.status === 'tekrar_istendi' ? 'warn' : 'neutral'}>
                  {a.status === 'tekrar_istendi' ? 'Tekrar teslim et' : 'Bekliyor'}
                </Pill>
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={CheckCircle2} title="Bekleyen ödevin yok" text="Yeni ödev atandığında burada göreceksin." />
        )}
      </Card>
    </>
  )
}

function GuardianDashboard({ data }) {
  return (
    <Card as={Link} to="/panel/cocuklarim">
      <Empty
        icon={Users}
        title={`${data.children_count} çocuğun bağlı`}
        text={data.redo_requested_total > 0
          ? `${data.redo_requested_total} ödev tekrar isteniyor. Detaylar için Çocuklarım'a git.`
          : 'İlerlemeyi görmek için Çocuklarım\'a git.'}
      />
    </Card>
  )
}

function MessagesPreview() {
  const { data: conversations } = useLoad(() => api.get('/messages/conversations'), [])
  const withUnread = conversations?.filter((c) => c.unread_count > 0) || []

  return (
    <Card>
      <div className="row-between row">
        <h3>Mesajlar</h3>
        <Link to="/panel/mesajlar" className="muted">Tümünü gör</Link>
      </div>
      {withUnread.length ? (
        <div className="list">
          {withUnread.map((c) => (
            <Link className="list-item" to={`/panel/mesajlar/${c.conversation_id}`} key={c.conversation_id}>
              <div className="grow">
                <strong>{c.peer.full_name}</strong>
                <div className="muted">{c.last_message}</div>
              </div>
              <Pill tone="accent">{c.unread_count}</Pill>
            </Link>
          ))}
        </div>
      ) : (
        <Empty icon={MessageCircle} title="Okunmamış mesaj yok" text="Yeni mesaj gönderip sohbeti başlatabilirsin." />
      )}
    </Card>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { data, loading } = useLoad(() => api.get('/dashboard'), [])

  return (
    <>
      <PageHeader title={`Merhaba, ${user.full_name.split(' ')[0]}`} />
      {loading || !data ? (
        <PageLoader />
      ) : (
        <>
          {data.role === 'teacher' && <TeacherDashboard data={data} />}
          {data.role === 'student' && <StudentDashboard data={data} />}
          {data.role === 'guardian' && <GuardianDashboard data={data} />}
        </>
      )}
      <MessagesPreview />
    </>
  )
}
