import { useState } from 'react'
import { Star } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from './hooks'
import { Button, Empty, ErrorNote, PageLoader, Sheet, TextArea, Toggle, useToast } from './ui.jsx'

function FilePreview({ file }) {
  if (file.kind === 'audio') return <audio controls src={file.url} className="submission-audio" />
  if (file.kind === 'image') return <img src={file.url} alt={file.original_name} className="submission-image" />
  return (
    <a className="btn btn-secondary" href={file.url} target="_blank" rel="noreferrer">
      {file.original_name || 'Dosyayı indir'}
    </a>
  )
}

export default function ReviewSubmissionSheet({ submissionId, studentName, onClose, onReviewed, readOnly = false }) {
  const { data: submission, loading, error, setData } = useLoad(() => api.get(`/submissions/${submissionId}`), [submissionId])
  const [score, setScore] = useState(0)
  const [feedback, setFeedback] = useState('')
  const [requestRedo, setRequestRedo] = useState(false)
  const [busy, setBusy] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const toast = useToast()

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setSaveError(null)
    try {
      const updated = await api.post(`/submissions/${submissionId}/review`, {
        score: score || null, feedback_text: feedback || null, request_redo: requestRedo,
      })
      setData(updated)
      toast('İnceleme kaydedildi')
      onReviewed?.()
    } catch (err) {
      setSaveError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Sheet title={studentName} onClose={onClose} wide>
      {loading ? (
        <PageLoader />
      ) : error || !submission ? (
        <ErrorNote error={error} />
      ) : submission.status === 'bekliyor' ? (
        <Empty title="Henüz teslim edilmedi" text="Öğrenci bu ödevi henüz göndermedi." />
      ) : (
        <div className="stack">
          {submission.text_content && <p className="submission-text">{submission.text_content}</p>}
          {submission.files?.length > 0 && (
            <div className="stack" style={{ gap: 10 }}>
              {submission.files.map((f) => <FilePreview file={f} key={f.id} />)}
            </div>
          )}

          {submission.reviews?.length > 0 && (
            <div className="stack" style={{ gap: 8 }}>
              {submission.reviews.map((r) => (
                <div className="review-note" key={r.id}>
                  <strong>{readOnly ? 'Eğitmen incelemesi' : 'Önceki inceleme'} · {new Date(r.created_at).toLocaleDateString('tr-TR')}:</strong> {r.score ? `${r.score}/5` : ''}
                  {r.feedback_text && <p>{r.feedback_text}</p>}
                </div>
              ))}
            </div>
          )}

          {!readOnly && (
            <form className="stack" onSubmit={submit}>
              <div className="field">
                <label>Puan</label>
                <div className="row star-row">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button type="button" key={n} className={`star-btn ${score >= n ? 'on' : ''}`} onClick={() => setScore(n)} aria-label={`${n} puan`}>
                      <Star size={22} fill={score >= n ? 'currentColor' : 'none'} />
                    </button>
                  ))}
                </div>
              </div>
              <TextArea label="Geri bildirim" value={feedback} onChange={(e) => setFeedback(e.target.value)}
                placeholder="Mahreç, akıcılık, tekrar edilmesi gereken kısımlar..." />
              <Toggle checked={requestRedo} onChange={setRequestRedo} label="Tekrar teslim istensin" />
              <ErrorNote error={saveError} />
              <Button variant="primary" busy={busy} type="submit" className="btn-block">İncelemeyi kaydet</Button>
            </form>
          )}
        </div>
      )}
    </Sheet>
  )
}
