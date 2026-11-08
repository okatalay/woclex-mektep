import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, FileText, Image as ImageIcon, Mic, Music, Paperclip, Square, Star, Trash2 } from 'lucide-react'

const KIND_ICON = { audio: Music, image: ImageIcon, file: FileText }
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, ErrorNote, PageHeader, PageLoader, Pill, TextArea, useToast } from '../components/ui.jsx'

const STATUS_LABEL = {
  bekliyor: 'Bekliyor', teslim_edildi: 'Teslim edildi', incelendi: 'İncelendi', tekrar_istendi: 'Tekrar teslim et',
}
const STATUS_TONE = { bekliyor: 'neutral', teslim_edildi: 'accent', incelendi: 'ok', tekrar_istendi: 'warn' }

function AudioRecorder({ onRecorded }) {
  const [recording, setRecording] = useState(false)
  const [error, setError] = useState(null)
  const recRef = useRef(null)
  const chunksRef = useRef([])

  async function start() {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream)
      chunksRef.current = []
      rec.ondataavailable = (e) => chunksRef.current.push(e.data)
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        onRecorded(new File([blob], `kayit-${Date.now()}.webm`, { type: 'audio/webm' }))
      }
      rec.start()
      recRef.current = rec
      setRecording(true)
    } catch {
      setError({ code: 'mic_denied' })
    }
  }

  function stop() {
    recRef.current?.stop()
    setRecording(false)
  }

  return (
    <div className="stack" style={{ gap: 8, alignItems: 'flex-start' }}>
      {!recording ? (
        <Button icon={Mic} onClick={start} type="button">Ses kaydı başlat</Button>
      ) : (
        <Button icon={Square} variant="danger" onClick={stop} type="button">Kaydı durdur</Button>
      )}
      {error && <small className="field-error">Mikrofona erişilemedi. Tarayıcı izinlerini kontrol et.</small>}
    </div>
  )
}

export default function AssignmentSubmit() {
  const { assignmentId } = useParams()
  const { data: assignment, loading: aLoading, error: aError } = useLoad(() => api.get(`/me/assignments/${assignmentId}`), [assignmentId])
  const { data: submission, loading: sLoading, error: sError, setData, reload } = useLoad(
    () => api.get(`/me/assignments/${assignmentId}/submission`), [assignmentId],
  )
  const [text, setText] = useState('')
  const [pendingFiles, setPendingFiles] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const toast = useToast()

  useEffect(() => {
    if (submission) setText(submission.text_content || '')
  }, [submission])

  if (aLoading || sLoading) return <PageLoader />
  if (aError || sError || !assignment) return <ErrorNote error={aError || sError} />

  const types = assignment.submission_types
  const canEdit = submission.status !== 'incelendi'

  async function removeSubmittedFile(fileId) {
    setBusy(true)
    try {
      const updated = await api.del(`/me/assignments/${assignmentId}/files/${fileId}`)
      setData(updated)
    } finally {
      setBusy(false)
    }
  }

  function addFiles(list) {
    setPendingFiles((f) => [...f, ...Array.from(list)])
  }

  function removeFile(i) {
    setPendingFiles((f) => f.filter((_, idx) => idx !== i))
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const fd = new FormData()
      if (types.includes('text') && text) fd.append('text_content', text)
      for (const f of pendingFiles) fd.append('files', f)
      const updated = await api.upload(`/me/assignments/${assignmentId}/submit`, fd)
      setData(updated)
      setPendingFiles([])
      toast('Ödev teslim edildi')
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Link to="/panel/odevlerim" className="back"><ChevronLeft size={16} aria-hidden="true" />Ödevlerim</Link>
      <PageHeader
        title={assignment.title}
        subtitle={assignment.due_at ? `Son tarih: ${new Date(assignment.due_at).toLocaleDateString('tr-TR')}` : undefined}
        actions={<Pill tone={STATUS_TONE[submission.status]}>{STATUS_LABEL[submission.status]}</Pill>}
      />
      {assignment.description && <Card><p>{assignment.description}</p></Card>}

      {assignment.attachments?.length > 0 && (
        <Card>
          <h3>Eğitmen materyali</h3>
          <div className="stack" style={{ gap: 10 }}>
            {assignment.attachments.map((f) => {
              const Icon = KIND_ICON[f.kind] || FileText
              return f.kind === 'audio'
                ? <audio controls src={f.url} key={f.id} className="submission-audio" />
                : (
                  <a className="btn btn-secondary" href={f.url} target="_blank" rel="noreferrer" key={f.id}>
                    <Icon size={16} aria-hidden="true" /> {f.original_name}
                  </a>
                )
            })}
          </div>
        </Card>
      )}

      {submission.reviews?.length > 0 && (
        <Card>
          <h3>Eğitmen geri bildirimleri</h3>
          <div className="stack">
            {submission.reviews.map((r) => (
              <div className="review-note" key={r.id}>
                {r.score && (
                  <div className="row star-row" aria-label={`${r.score}/5`}>
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star key={n} size={18} fill={r.score >= n ? 'currentColor' : 'none'} className={r.score >= n ? 'star-on' : 'star-off'} />
                    ))}
                  </div>
                )}
                {r.feedback_text && <p>{r.feedback_text}</p>}
                <small className="muted">{new Date(r.created_at).toLocaleString('tr-TR')}</small>
              </div>
            ))}
          </div>
        </Card>
      )}

      {(submission.text_content || submission.files?.length > 0) && (
        <Card>
          <h3>Gönderdiğin teslim</h3>
          {submission.text_content && <p className="submission-text">{submission.text_content}</p>}
          {submission.files?.length > 0 && (
            <ul className="pending-files">
              {submission.files.map((f) => (
                <li key={f.id}>
                  {f.kind === 'audio'
                    ? <audio controls src={f.url} className="submission-audio" />
                    : <a className="btn btn-secondary" href={f.url} target="_blank" rel="noreferrer">{f.original_name}</a>}
                  {canEdit && (
                    <button type="button" className="icon-btn" disabled={busy} onClick={() => removeSubmittedFile(f.id)} aria-label="Kaldır">
                      <Trash2 size={16} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {canEdit && (
        <Card>
          <h3>{submission.status === 'bekliyor' ? 'Teslim et' : 'Ekle / güncelle'}</h3>
          <form className="stack" onSubmit={submit}>
            {types.includes('text') && (
              <TextArea label="Metin" hideLabel value={text} onChange={(e) => setText(e.target.value)} placeholder="Notunu buraya yaz..." />
            )}
            <div className="row">
              {types.includes('audio') && <AudioRecorder onRecorded={(f) => setPendingFiles((p) => [...p, f])} />}
              {(types.includes('file') || types.includes('image')) && (
                <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                  <Paperclip size={16} aria-hidden="true" /> Dosya / fotoğraf ekle
                  <input type="file" hidden multiple onChange={(e) => addFiles(e.target.files)} />
                </label>
              )}
            </div>
            {pendingFiles.length > 0 && (
              <ul className="pending-files">
                {pendingFiles.map((f, i) => (
                  <li key={i}>
                    {f.type.startsWith('audio') ? <audio controls src={URL.createObjectURL(f)} /> : <span>{f.name}</span>}
                    <button type="button" className="icon-btn" onClick={() => removeFile(i)} aria-label="Kaldır"><Trash2 size={16} /></button>
                  </li>
                ))}
              </ul>
            )}
            <ErrorNote error={error} />
            <div className="row">
              <Button variant="primary" busy={busy} type="submit">Teslim et</Button>
            </div>
          </form>
        </Card>
      )}
    </>
  )
}
