import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, MapPin, Pencil, Plus, Trash2, ArrowUp, ArrowDown } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import ArchiveAttach from '../components/ArchiveAttach.jsx'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Pill, Sheet, TextArea, TextField, useConfirm, useToast } from '../components/ui.jsx'

const TYPE_OPTIONS = [
  { value: 'audio', label: 'Ses kaydı' },
  { value: 'text', label: 'Metin' },
  { value: 'file', label: 'Dosya / fotoğraf' },
]

function StopFormFields({ title, setTitle, description, setDescription, types, setTypes }) {
  function toggleType(v) {
    setTypes((t) => (t.includes(v) ? t.filter((x) => x !== v) : [...t, v]))
  }
  return (
    <>
      <TextField label="Durak adı" value={title} onChange={(e) => setTitle(e.target.value)}
        placeholder="Örn. Tecvid Bul 01" autoFocus required minLength={2} />
      <TextArea label="Açıklama (opsiyonel)" value={description} onChange={(e) => setDescription(e.target.value)}
        placeholder="Bu durakta öğrenciden ne bekleniyor?" />
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
    </>
  )
}

function CreateStopSheet({ routeId, onClose, onCreated }) {
  const [archiveIds, setArchiveIds] = useState([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [types, setTypes] = useState(['audio', 'text', 'file'])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    if (!types.length) {
      setError({ code: 'invalid' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      const stop = await api.post(`/routes/${routeId}/stops`, { title, description: description || null, submission_types: types })
      if (archiveIds.length) await api.post(`/assignments/${stop.assignment_id}/attachments/from-archive`, { item_ids: archiveIds })
      onCreated(stop)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni durak" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <ArchiveAttach value={archiveIds} onChange={setArchiveIds} />
        <StopFormFields title={title} setTitle={setTitle} description={description} setDescription={setDescription} types={types} setTypes={setTypes} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Durağı ekle</Button>
      </form>
    </Sheet>
  )
}

function EditStopSheet({ routeId, stop, onClose, onUpdated }) {
  const [title, setTitle] = useState(stop.title)
  const [description, setDescription] = useState(stop.description || '')
  const [types, setTypes] = useState(stop.submission_types)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    if (!types.length) {
      setError({ code: 'invalid' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      const updated = await api.patch(`/routes/${routeId}/stops/${stop.stop_id}`, { title, description: description || null, submission_types: types })
      onUpdated(updated)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Durağı düzenle" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <StopFormFields title={title} setTitle={setTitle} description={description} setDescription={setDescription} types={types} setTypes={setTypes} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Kaydet</Button>
      </form>
    </Sheet>
  )
}

export default function RouteDetail() {
  const { id, routeId } = useParams()
  const { data: route, loading, error, reload } = useLoad(() => api.get(`/routes/${routeId}`), [routeId])
  const [addingStop, setAddingStop] = useState(false)
  const [editingStop, setEditingStop] = useState(null)
  const [busyStopId, setBusyStopId] = useState(null)
  const confirm = useConfirm()
  const toast = useToast()

  if (loading) return <PageLoader />
  if (error || !route) return <ErrorNote error={error} />

  async function move(stopId, direction) {
    setBusyStopId(stopId)
    try {
      await api.post(`/routes/${routeId}/stops/${stopId}/move`, { direction })
      reload()
    } finally {
      setBusyStopId(null)
    }
  }

  async function removeStop(stop) {
    const ok = await confirm({
      title: 'Durağı sil',
      text: `"${stop.title}" durağı ve o durağa ait tüm teslimler silinecek. Bu işlem geri alınamaz.`,
      danger: true,
      confirmLabel: 'Sil',
    })
    if (!ok) return
    setBusyStopId(stop.stop_id)
    try {
      await api.del(`/routes/${routeId}/stops/${stop.stop_id}`)
      toast('Durak silindi')
      reload()
    } finally {
      setBusyStopId(null)
    }
  }

  return (
    <>
      <Link to={`/panel/siniflar/${id}`} className="back"><ChevronLeft size={16} aria-hidden="true" />Sınıfa dön</Link>
      <PageHeader
        title={route.title}
        subtitle={route.description || `${route.stop_count} durak`}
        actions={<Button variant="primary" icon={Plus} onClick={() => setAddingStop(true)}>Durak ekle</Button>}
      />

      {route.stops.length ? (
        <div className="route-timeline">
          {route.stops.map((s, i) => (
            <div className="route-node" key={s.stop_id}>
              <div className="route-node-rail">
                <span className="route-node-dot">{i + 1}</span>
                {i < route.stops.length - 1 && <span className="route-node-line" />}
              </div>
              <Card className="route-node-card">
                <div className="row-between row">
                  <Link to={`/panel/siniflar/${id}/odevler/${s.assignment_id}`} className="grow" style={{ color: 'var(--ink)' }}>
                    <strong>{s.title}</strong>
                  </Link>
                  <div className="row" style={{ gap: 2 }}>
                    <button className="icon-btn" disabled={i === 0 || busyStopId === s.stop_id} onClick={() => move(s.stop_id, 'up')} aria-label="Yukarı taşı">
                      <ArrowUp size={16} />
                    </button>
                    <button className="icon-btn" disabled={i === route.stops.length - 1 || busyStopId === s.stop_id} onClick={() => move(s.stop_id, 'down')} aria-label="Aşağı taşı">
                      <ArrowDown size={16} />
                    </button>
                    <button className="icon-btn" disabled={busyStopId === s.stop_id} onClick={() => setEditingStop(s)} aria-label="Düzenle">
                      <Pencil size={16} />
                    </button>
                    <button className="icon-btn" disabled={busyStopId === s.stop_id} onClick={() => removeStop(s)} aria-label="Sil">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                {s.description && <p className="muted" style={{ margin: '4px 0 0' }}>{s.description}</p>}
                <div className="row" style={{ marginTop: 8, justifyContent: 'space-between' }}>
                  <Pill tone={s.reviewed_count === s.target_count && s.target_count > 0 ? 'ok' : s.submitted_count > 0 ? 'accent' : 'neutral'}>
                    {s.reviewed_count}/{s.target_count} incelendi
                  </Pill>
                  <Link to={`/panel/siniflar/${id}/odevler/${s.assignment_id}`} className="muted" style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
                    Teslimleri gör <ChevronRight size={14} aria-hidden="true" />
                  </Link>
                </div>
              </Card>
            </div>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={MapPin} title="Henüz durak yok" text="Öğrencinin sırayla ilerleyeceği ilk durağı ekle." />
        </Card>
      )}

      {addingStop && (
        <CreateStopSheet
          routeId={routeId}
          onClose={() => setAddingStop(false)}
          onCreated={() => { setAddingStop(false); reload() }}
        />
      )}
      {editingStop && (
        <EditStopSheet
          routeId={routeId}
          stop={editingStop}
          onClose={() => setEditingStop(null)}
          onUpdated={() => { setEditingStop(null); toast('Durak güncellendi'); reload() }}
        />
      )}
    </>
  )
}
