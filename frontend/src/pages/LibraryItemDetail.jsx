import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ChevronLeft, FileText, Image as ImageIcon, Music, Paperclip, Send, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, ErrorNote, PageHeader, PageLoader, useConfirm, useToast } from '../components/ui.jsx'
import AssignToClassSheet from '../components/AssignToClassSheet.jsx'

const KIND_ICON = { audio: Music, image: ImageIcon, file: FileText }

export default function LibraryItemDetail() {
  const { id } = useParams()
  const { data: item, loading, error, reload } = useLoad(() => api.get(`/library/${id}`), [id])
  const [uploading, setUploading] = useState(false)
  const [assigning, setAssigning] = useState(false)
  const confirm = useConfirm()
  const toast = useToast()
  const nav = useNavigate()

  if (loading) return <PageLoader />
  if (error || !item) return <ErrorNote error={error} />

  const isArchive = item.kind === 'arsiv'
  const base = isArchive ? '/panel/arsiv' : '/panel/tilavet'

  async function upload(e) {
    const files = e.target.files
    if (!files.length) return
    setUploading(true)
    try {
      const fd = new FormData()
      for (const f of files) fd.append('files', f)
      await api.upload(`/library/${id}/files`, fd)
      reload()
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function removeFile(fileId) {
    await api.del(`/library/${id}/files/${fileId}`)
    reload()
  }

  async function removeItem() {
    const ok = await confirm({ title: isArchive ? 'Arşivden sil' : 'Tilavet sil', text: `"${item.title}" silinecek.`, danger: true, confirmLabel: 'Sil' })
    if (!ok) return
    await api.del(`/library/${id}`)
    toast('Silindi')
    nav(base)
  }

  return (
    <>
      <Link to={base} className="back"><ChevronLeft size={16} aria-hidden="true" />{isArchive ? 'Arşiv' : 'Tilavet'}</Link>
      <PageHeader
        title={item.title}
        subtitle={item.description}
        actions={
          <>
            {!isArchive && <Button variant="primary" icon={Send} onClick={() => setAssigning(true)}>Sınıfa/öğrenciye ata</Button>}
            <Button variant="danger-quiet" icon={Trash2} onClick={removeItem}>{isArchive ? 'Arşivden sil' : 'Tilavet sil'}</Button>
          </>
        }
      />

      <Card>
        <div className="row-between row">
          <h3>Dosyalar</h3>
          <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
            <Paperclip size={16} aria-hidden="true" /> Ses / görsel / not dosyası ekle
            <input type="file" hidden multiple disabled={uploading} onChange={upload} />
          </label>
        </div>
        {item.files?.length ? (
          <ul className="pending-files">
            {item.files.map((f) => {
              const Icon = KIND_ICON[f.kind] || FileText
              return (
                <li key={f.id}>
                  {f.kind === 'audio'
                    ? <audio controls src={f.url} className="submission-audio" />
                    : <a href={f.url} target="_blank" rel="noreferrer" className="row" style={{ gap: 6 }}><Icon size={16} aria-hidden="true" /> {f.original_name}</a>}
                  <button type="button" className="icon-btn" onClick={() => removeFile(f.id)} aria-label="Kaldır"><Trash2 size={16} /></button>
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="muted">Henüz dosya eklenmedi.</p>
        )}
      </Card>

      {assigning && (
        <AssignToClassSheet
          title={`"${item.title}" ata`}
          submitLabel="Ödev olarak ata"
          onClose={() => setAssigning(false)}
          onAssigned={() => setAssigning(false)}
          onSubmit={(classroomId, studentIds, dueAt) =>
            api.post(`/library/${id}/assign`, { classroom_id: classroomId, student_ids: studentIds, due_at: dueAt })
          }
        />
      )}
    </>
  )
}
