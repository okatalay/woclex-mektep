import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, ChevronRight, Plus } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import ArchiveAttach from '../components/ArchiveAttach.jsx'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Sheet, TextArea, TextField, useToast } from '../components/ui.jsx'

const KINDS = {
  tilavet: {
    base: '/panel/tilavet', title: 'Tilavet',
    subtitle: 'Ses/görsel/not ekle, tek tıkla sınıfa veya seçili öğrencilere ata.',
    create: 'Yeni tilavet', sheet: 'Yeni tilavet', submit: 'Tilavet ekle', toast: 'Tilavet eklendi',
    placeholder: 'Örn. Bakara Suresi 1-5', empty: 'Henüz tilavet yok', emptyText: 'Sık kullandığın tilavetleri ekle; sonra tek tıkla ata.',
  },
  arsiv: {
    base: '/panel/arsiv', title: 'Arşiv',
    subtitle: 'Dosya ve notların; tilavet, ödev ve rota oluştururken buradan seçebilirsin.',
    create: 'Yeni içerik', sheet: 'Arşive içerik ekle', submit: 'Arşive ekle', toast: 'Arşive eklendi',
    placeholder: 'Örn. Harf kartları', empty: 'Arşiv boş', emptyText: 'Sık kullandığın ses, görsel ve notları buraya ekle.',
  },
}

function CreateLibraryItemSheet({ kind, onClose, onCreated }) {
  const k = KINDS[kind]
  const [archiveIds, setArchiveIds] = useState([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const item = await api.post('/library', { kind, title, description: description || null })
      if (archiveIds.length) await api.post(`/library/${item.id}/files/from-archive`, { item_ids: archiveIds })
      onCreated(item)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title={k.sheet} onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        {kind === 'tilavet' && <ArchiveAttach value={archiveIds} onChange={setArchiveIds} />}
        <TextField label="Başlık" value={title} onChange={(e) => setTitle(e.target.value)}
          placeholder={k.placeholder} autoFocus required minLength={2} />
        <TextArea label="Açıklama (opsiyonel)" value={description} onChange={(e) => setDescription(e.target.value)}
          placeholder="Notlar, ayet aralığı, ne bekleniyor..." />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">{k.submit}</Button>
      </form>
    </Sheet>
  )
}

export default function Library({ kind }) {
  const k = KINDS[kind]
  const { data: items, loading, error, reload } = useLoad(() => api.get(`/library?kind=${kind}`), [kind])
  const [creating, setCreating] = useState(false)
  const toast = useToast()

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader
        title={k.title}
        subtitle={k.subtitle}
        actions={<Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>{k.create}</Button>}
      />
      <ErrorNote error={error} />
      {items?.length ? (
        <div className="list">
          {items.map((i) => (
            <Link className="list-item" to={`${k.base}/${i.id}`} key={i.id}>
              <div className="grow">
                <strong>{i.title}</strong>
                {i.description && <div className="muted">{i.description}</div>}
              </div>
              <ChevronRight size={18} aria-hidden="true" className="muted" />
            </Link>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={BookOpen} title={k.empty} text={k.emptyText} />
        </Card>
      )}
      {creating && (
        <CreateLibraryItemSheet
          kind={kind}
          onClose={() => setCreating(false)}
          onCreated={() => { setCreating(false); toast(k.toast); reload() }}
        />
      )}
    </>
  )
}
