import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, NotebookPen } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Card, Empty, ErrorNote, PageHeader, PageLoader, Pill } from '../components/ui.jsx'
import ReviewSubmissionSheet from '../components/ReviewSubmissionSheet.jsx'
import TrackingSummary from '../components/TrackingSummary.jsx'
import CurriculumChart from '../components/CurriculumChart.jsx'
import PageLogSection from '../components/PageLogSection.jsx'

const STATUS_LABEL = {
  bekliyor: 'Bekliyor', teslim_edildi: 'İncelenecek', incelendi: 'İncelendi', tekrar_istendi: 'Tekrar istendi',
}
const STATUS_TONE = { bekliyor: 'neutral', teslim_edildi: 'accent', incelendi: 'ok', tekrar_istendi: 'warn' }

export default function ChildDetail() {
  const { studentId } = useParams()
  const { data: children } = useLoad(() => api.get('/guardians/me/children'), [])
  const { data: assignments, loading, error } = useLoad(
    () => api.get(`/guardians/children/${studentId}/assignments`), [studentId],
  )
  const { data: summary } = useLoad(() => api.get(`/students/${studentId}/tracking-summary`), [studentId])
  const [viewing, setViewing] = useState(null)
  const child = children?.find((c) => c.student_id === studentId)

  if (loading) return <PageLoader />

  return (
    <>
      <Link to="/panel/cocuklarim" className="back"><ChevronLeft size={16} aria-hidden="true" />Çocuklarım</Link>
      <PageHeader title={child?.full_name || 'Öğrenci'} subtitle="Ödev geçmişi ve teslimler." />
      <ErrorNote error={error} />

      {summary && (
        <Card>
          <h3>Genel bakış</h3>
          <TrackingSummary summary={summary} />
        </Card>
      )}

      <Card>
        <h3>Ödevler</h3>
        {assignments?.length ? (
          <div className="list">
            {assignments.map((a) => (
              <button
                className="list-item as-row"
                key={a.id}
                disabled={a.status === 'bekliyor'}
                onClick={() => a.status !== 'bekliyor' && setViewing(a)}
              >
                <div className="grow">
                  <strong>{a.title}</strong>
                  {a.submitted_at && <div className="muted">{new Date(a.submitted_at).toLocaleString('tr-TR')}</div>}
                </div>
                <Pill tone={STATUS_TONE[a.status]}>{STATUS_LABEL[a.status]}</Pill>
              </button>
            ))}
          </div>
        ) : (
          <Empty icon={NotebookPen} title="Henüz ödev yok" text="Öğrenciye ödev atandığında burada görünecek." />
        )}
      </Card>

      <PageLogSection studentId={studentId} />

      <h3>Ezber çizelgesi</h3>
      <CurriculumChart endpoint={`/guardians/children/${studentId}/curriculum?kind=ezber`} />

      <h3>Cüz &amp; tecvid çizelgesi</h3>
      <CurriculumChart endpoint={`/guardians/children/${studentId}/curriculum?kind=tecvid`} />

      {viewing && (
        <ReviewSubmissionSheet
          submissionId={viewing.submission_id}
          studentName={viewing.title}
          onClose={() => setViewing(null)}
          readOnly
        />
      )}
    </>
  )
}
