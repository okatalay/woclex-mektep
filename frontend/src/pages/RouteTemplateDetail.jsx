import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ChevronLeft, MapPin, Plus, Send, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Sheet, TextArea, TextField, useConfirm, useToast } from '../components/ui.jsx'
import AssignToClassSheet from '../components/AssignToClassSheet.jsx'

const TYPE_OPTIONS = [
  { value: 'audio', label: 'Ses kaydı' },
  { value: 'text', label: 'Metin' },
  { value: 'file', label: 'Dosya / fotoğraf' },
]

function AddStopSheet({ templateId, onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [types, setTypes] = useState(['audio', 'text', 'file'])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  function toggleType(v) {
    setTypes((t) => (t.includes(v) ? t.filter((x) => x !== v) : [...t, v]))
  }

  async function submit(e) {
    e.preventDefault()
    if (!types.length) {
      setError({ code: 'invalid_submission_types' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      const stop = await api.post(`/route-templates/${templateId}/stops`, { title, description: description || null, submission_types: types })
      onCreated(stop)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Durak ekle" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <TextField label="Durak adı" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus required minLength={2} />
        <TextArea label="Açıklama (opsiyonel)" value={description} onChange={(e) => setDescription(e.target.value)} />
        <div className="field">
          <label>Teslim türleri</label>
          <div className="row">
            {TYPE_OPTIONS.map((o) => (
              <label key={o.value} className={`type-chip ${types.includes(o.value) ? 'on' : ''}`}>
                <input type="checkbox" checked={types.includes(o.value)} onChange={() => toggleType(o.value)} />
                {o.label}
              </label>
            ))}
          </div>
        </div>
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Durağı ekle</Button>
      </form>
    </Sheet>
  )
}

export default function RouteTemplateDetail() {
  const { id } = useParams()
  const { data: template, loading, error, reload } = useLoad(() => api.get(`/route-templates/${id}`), [id])
  const [addingStop, setAddingStop] = useState(false)
  const [applying, setApplying] = useState(false)
  const confirm = useConfirm()
  const toast = useToast()
  const nav = useNavigate()

  if (loading) return <PageLoader />
  if (error || !template) return <ErrorNote error={error} />

  async function removeStop(stop) {
    const ok = await confirm({ title: 'Durağı sil', text: `"${stop.title}" şablondan silinecek.`, danger: true, confirmLabel: 'Sil' })
    if (!ok) return
    await api.del(`/route-templates/${id}/stops/${stop.id}`)
    reload()
  }

  async function removeTemplate() {
    const ok = await confirm({ title: 'Şablonu sil', text: `"${template.title}" şablonu silinecek.`, danger: true, confirmLabel: 'Sil' })
    if (!ok) return
    await api.del(`/route-templates/${id}`)
    toast('Silindi')
    nav('/panel/rota-arsivi')
  }

  return (
    <>
      <Link to="/panel/rota-arsivi" className="back"><ChevronLeft size={16} aria-hidden="true" />Rota</Link>
      <PageHeader
        title={template.title}
        subtitle={template.description}
        actions={
          <>
            <Button variant="primary" icon={Send} onClick={() => setApplying(true)}>Sınıfa/öğrenciye uygula</Button>
            <Button variant="danger-quiet" icon={Trash2} onClick={removeTemplate}>Şablonu sil</Button>
          </>
        }
      />

      <Card>
        <div className="row-between row">
          <h3>Duraklar</h3>
          <Button icon={Plus} onClick={() => setAddingStop(true)}>Durak ekle</Button>
        </div>
        {template.stops?.length ? (
          <div className="list">
            {template.stops.map((s, i) => (
              <div className="list-item as-row" key={s.id}>
                <div className="grow">
                  <strong>{i + 1}. {s.title}</strong>
                  {s.description && <div className="muted">{s.description}</div>}
                </div>
                <button className="icon-btn" onClick={() => removeStop(s)} aria-label="Sil"><Trash2 size={16} /></button>
              </div>
            ))}
          </div>
        ) : (
          <Empty icon={MapPin} title="Henüz durak yok" text="Şablona en az bir durak ekle." />
        )}
      </Card>

      {addingStop && (
        <AddStopSheet templateId={id} onClose={() => setAddingStop(false)} onCreated={() => { setAddingStop(false); reload() }} />
      )}
      {applying && (
        <AssignToClassSheet
          title={`"${template.title}" uygula`}
          submitLabel="Rotayı oluştur"
          withDueDate={false}
          onClose={() => setApplying(false)}
          onAssigned={() => setApplying(false)}
          onSubmit={(classroomId, studentIds) =>
            api.post(`/route-templates/${id}/apply`, { classroom_id: classroomId, student_ids: studentIds })
          }
        />
      )}
    </>
  )
}
