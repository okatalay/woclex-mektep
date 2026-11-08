import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CalendarCheck, ChevronLeft, UserMinus, UserPlus, Users } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, useConfirm, useToast } from '../components/ui.jsx'
import GuardianInviteSheet from '../components/GuardianInviteSheet.jsx'
import ProgressStats from '../components/ProgressStats.jsx'
import TrackingSummary from '../components/TrackingSummary.jsx'
import CurriculumChart from '../components/CurriculumChart.jsx'
import PageLogSection from '../components/PageLogSection.jsx'

export default function StudentDetail() {
  const { id, studentId } = useParams()
  const nav = useNavigate()
  const { data: student, loading, error, reload } = useLoad(() => api.get(`/classes/${id}/students/${studentId}`), [id, studentId])
  const { data: summary } = useLoad(() => api.get(`/students/${studentId}/tracking-summary`), [studentId])
  const [inviting, setInviting] = useState(false)
  const confirm = useConfirm()
  const toast = useToast()

  if (loading) return <PageLoader />
  if (error || !student) return <ErrorNote error={error} />

  async function removeStudent() {
    const ok = await confirm({
      title: 'Öğrenciyi sınıftan çıkar',
      text: `${student.full_name} bu sınıftan çıkarılacak. Bu işlem geri alınamaz.`,
      danger: true,
      confirmLabel: 'Çıkar',
    })
    if (!ok) return
    await api.post(`/classes/${id}/students/${studentId}/remove`)
    toast('Öğrenci sınıftan çıkarıldı')
    nav(`/panel/siniflar/${id}`, { replace: true })
  }

  return (
    <>
      <Link to={`/panel/siniflar/${id}`} className="back"><ChevronLeft size={16} aria-hidden="true" />Sınıfa dön</Link>
      <PageHeader
        title={student.full_name}
        subtitle={`@${student.username} · Katılım: ${new Date(student.joined_at).toLocaleDateString('tr-TR')}`}
        actions={
          <>
            <Link to={`/panel/siniflar/${id}/yoklama`} className="btn btn-secondary"><CalendarCheck size={16} aria-hidden="true" /> Yoklama</Link>
            <Button icon={UserPlus} onClick={() => setInviting(true)}>Veli davet et</Button>
            <Button variant="danger-quiet" icon={UserMinus} onClick={removeStudent}>Sınıftan çıkar</Button>
          </>
        }
      />

      <Card>
        <h3>Ödevler ve gelişim</h3>
        <ProgressStats progress={student.progress} />
      </Card>

      {summary && (
        <Card>
          <h3>Genel bakış</h3>
          <TrackingSummary summary={summary} />
        </Card>
      )}

      <Card>
        <h3>Veliler</h3>
        {student.guardians.length ? (
          <div className="list">
            {student.guardians.map((g) => (
              <div className="list-item" key={g.guardian_id}>
                <div className="grow">
                  <strong>{g.full_name}</strong>
                  <div className="muted">@{g.username}{g.relation ? ` · ${g.relation}` : ''}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <Empty icon={Users} title="Henüz veli bağlı değil" text="Bir davet linki oluşturup veliyle paylaş." />
        )}
      </Card>

      <PageLogSection studentId={studentId} editable />

      <h3>Ezber çizelgesi</h3>
      <CurriculumChart endpoint={`/curriculum?kind=ezber&student_id=${studentId}`} studentId={studentId} editable />

      <h3>Cüz &amp; tecvid çizelgesi</h3>
      <CurriculumChart endpoint={`/curriculum?kind=tecvid&student_id=${studentId}`} studentId={studentId} editable />

      {inviting && (
        <GuardianInviteSheet
          classroomId={id}
          student={student}
          onClose={() => { setInviting(false); reload() }}
        />
      )}
    </>
  )
}
