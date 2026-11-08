import { useState } from 'react'
import { Paperclip, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { Button, ErrorNote, Sheet, TextArea, TextField, useToast } from './ui.jsx'
import StudentPicker from './StudentPicker.jsx'
import ArchiveAttach from './ArchiveAttach.jsx'

const TYPE_OPTIONS = [
  { value: 'audio', label: 'Ses kaydı' },
  { value: 'text', label: 'Metin' },
  { value: 'file', label: 'Dosya / fotoğraf' },
]

export default function CreateAssignmentSheet({ classroomId, onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [dueAt, setDueAt] = useState('')
  const [types, setTypes] = useState(['audio', 'text', 'file'])
  const [studentIds, setStudentIds] = useState(null)
  const [materials, setMaterials] = useState([])
  const [archiveIds, setArchiveIds] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const toast = useToast()

  function toggleType(v) {
    setTypes((t) => (t.includes(v) ? t.filter((x) => x !== v) : [...t, v]))
  }

  function addMaterials(list) {
    setMaterials((m) => [...m, ...Array.from(list)])
  }

  function removeMaterial(i) {
    setMaterials((m) => m.filter((_, idx) => idx !== i))
  }

  async function submit(e) {
    e.preventDefault()
    if (!types.length) {
      setError({ code: 'invalid_submission_types' })
      return
    }
    if (studentIds !== null && studentIds.length === 0) {
      setError({ code: 'no_valid_students' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      const a = await api.post(`/classes/${classroomId}/assignments`, {
        title,
        description: description || null,
        submission_types: types,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
        student_ids: studentIds,
      })
      if (materials.length) {
        const fd = new FormData()
        for (const f of materials) fd.append('files', f)
        await api.upload(`/assignments/${a.id}/attachments`, fd)
      }
      if (archiveIds.length) await api.post(`/assignments/${a.id}/attachments/from-archive`, { item_ids: archiveIds })
      toast('Ödev oluşturuldu')
      onCreated(a)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni ödev" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <ArchiveAttach value={archiveIds} onChange={setArchiveIds} />
        <TextField label="Başlık" value={title} onChange={(e) => setTitle(e.target.value)}
          placeholder="Örn. Bakara Suresi 1-5. ayet tilaveti" autoFocus required minLength={2} />
        <TextArea label="Açıklama (opsiyonel)" value={description} onChange={(e) => setDescription(e.target.value)}
          placeholder="Ne bekleniyor, hangi sayfa/ayet aralığı..." />
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
        <StudentPicker classroomId={classroomId} value={studentIds} onChange={setStudentIds} />
        <div className="field">
          <label>Materyal (opsiyonel)</label>
          <label className="btn btn-secondary" style={{ width: 'fit-content', cursor: 'pointer' }}>
            <Paperclip size={16} aria-hidden="true" /> Ses / görsel / dosya ekle
            <input type="file" hidden multiple onChange={(e) => addMaterials(e.target.files)} />
          </label>
          {materials.length > 0 && (
            <ul className="pending-files">
              {materials.map((f, i) => (
                <li key={i}>
                  <span>{f.name}</span>
                  <button type="button" className="icon-btn" onClick={() => removeMaterial(i)} aria-label="Kaldır"><Trash2 size={16} /></button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <TextField label="Son teslim tarihi (opsiyonel)" type="date" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Ödevi oluştur ve ata</Button>
      </form>
    </Sheet>
  )
}
