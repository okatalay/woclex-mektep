import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, FileText, Image as ImageIcon, Music, Paperclip, Trash2, Users } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Pill, useToast } from '../components/ui.jsx'
import ReviewSubmissionSheet from '../components/ReviewSubmissionSheet.jsx'

const KIND_ICON = { audio: Music, image: ImageIcon, file: FileText }

function MaterialsCard({ assignment, onChanged }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)

  async function upload(e) {
    const files = e.target.files
    if (!files.length) return
    setBusy(true)
    try {
      const fd = new FormData()
      for (const f of files) fd.append('files', f)
      await api.upload(`/assignments/${assignment.id}/attachments`, fd)
      toast('Materyal eklendi')
      onChanged()
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  async function remove(attId) {
    setBusy(true)
    try {
      await api.del(`/assignments/${assignment.id}/attachments/${attId}`)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <div className="row-between row">
        <h3>Materyal</h3>
        <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
          <Paperclip size={16} aria-hidden="true" /> Ekle
          <input type="file" hidden multiple disabled={busy} onChange={upload} />
        </label>
      </div>
      {assignment.attachments?.length ? (
        <ul className="pending-files">
          {assignment.attachments.map((f) => {
            const Icon = KIND_ICON[f.kind] || FileText
            return (
              <li key={f.id}>
                <a href={f.url} target="_blank" rel="noreferrer" className="row" style={{ gap: 6 }}>
                  <Icon size={16} aria-hidden="true" /> {f.original_name}
                </a>
                <button type="button" className="icon-btn" disabled={busy} onClick={() => remove(f.id)} aria-label="Kaldır"><Trash2 size={16} /></button>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="muted">Henüz materyal eklenmedi.</p>
      )}
    </Card>
  )
}

const STATUS_LABEL = {
  bekliyor: 'Bekliyor',
  teslim_edildi: 'İncelenecek',
  incelendi: 'İncelendi',
  tekrar_istendi: 'Tekrar istendi',
}
const STATUS_TONE = {
  bekliyor: 'neutral',
  teslim_edildi: 'accent',
  incelendi: 'ok',
  tekrar_istendi: 'warn',
}

export default function AssignmentDetail() {
  const { id, assignmentId } = useParams()
  const { data: assignment, loading, error, reload } = useLoad(() => api.get(`/assignments/${assignmentId}`), [assignmentId])
  const [reviewing, setReviewing] = useState(null)

  if (loading) return <PageLoader />
  if (error || !assignment) return <ErrorNote error={error} />

  return (
    <>
      <Link to={`/panel/siniflar/${id}`} className="back"><ChevronLeft size={16} aria-hidden="true" />Sınıfa dön</Link>
      <PageHeader
        title={assignment.title}
        subtitle={assignment.due_at ? `Son tarih: ${new Date(assignment.due_at).toLocaleDateString('tr-TR')}` : 'Süre sınırı yok'}
      />
      {assignment.description && <Card><p>{assignment.description}</p></Card>}

      <MaterialsCard assignment={assignment} onChanged={reload} />

      <Card>
        <h3>Teslimler</h3>
        {assignment.submissions?.length ? (
          <div className="list">
            {assignment.submissions.map((s) => (
              <button className="list-item as-row" key={s.submission_id} onClick={() => setReviewing(s)}>
                <div className="grow">
                  <strong>{s.full_name}</strong>
                  {s.submitted_at && <div className="muted">{new Date(s.submitted_at).toLocaleString('tr-TR')}</div>}
                </div>
                <Pill tone={STATUS_TONE[s.status]}>{STATUS_LABEL[s.status]}</Pill>
              </button>
            ))}
          </div>
        ) : (
          <Empty icon={Users} title="Öğrenci yok" text="Bu ödev kimseye atanmadı." />
        )}
      </Card>

      {reviewing && (
        <ReviewSubmissionSheet
          submissionId={reviewing.submission_id}
          studentName={reviewing.full_name}
          onClose={() => setReviewing(null)}
          onReviewed={reload}
        />
      )}
    </>
  )
}
