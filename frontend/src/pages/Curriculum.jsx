import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Segmented, Sheet, TextField, useConfirm, useToast } from '../components/ui.jsx'

const KIND_OPTIONS = [{ value: 'ezber', label: 'Ezber Çizelgesi' }, { value: 'tecvid', label: 'Cüz & Tecvid Çizelgesi' }]

function CreateCategorySheet({ kind, onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const cat = await api.post('/curriculum/categories', { kind, title })
      onCreated(cat)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni başlık" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <TextField label="Başlık" value={title} onChange={(e) => setTitle(e.target.value)}
          placeholder="Örn. SEVİYE 1" autoFocus required minLength={2} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Ekle</Button>
      </form>
    </Sheet>
  )
}

function AddItemRow({ categoryId, onAdded }) {
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!title.trim()) return
    setBusy(true)
    try {
      await api.post(`/curriculum/categories/${categoryId}/items`, { title: title.trim() })
      setTitle('')
      onAdded()
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="row" onSubmit={submit} style={{ marginTop: 8 }}>
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Yeni konu ekle..." style={{ flex: 1 }} />
      <Button busy={busy} type="submit" icon={Plus}>Ekle</Button>
    </form>
  )
}

export default function Curriculum() {
  const [kind, setKind] = useState('ezber')
  const { data: categories, loading, error, reload } = useLoad(() => api.get(`/curriculum/categories?kind=${kind}`), [kind])
  const [creating, setCreating] = useState(false)
  const confirm = useConfirm()
  const toast = useToast()

  async function removeCategory(cat) {
    const ok = await confirm({ title: 'Başlığı sil', text: `"${cat.title}" ve altındaki tüm konular silinecek.`, danger: true, confirmLabel: 'Sil' })
    if (!ok) return
    await api.del(`/curriculum/categories/${cat.id}`)
    reload()
  }

  async function removeItem(itemId) {
    await api.del(`/curriculum/items/${itemId}`)
    reload()
  }

  return (
    <>
      <PageHeader
        title="Müfredat"
        subtitle="Ezber ve tecvid çizelgesindeki başlık/konuları buradan yönet; öğrenci durumu öğrenci kartından işaretlenir."
        actions={<Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>Yeni başlık</Button>}
      />

      <Segmented value={kind} onChange={setKind} options={KIND_OPTIONS} label="Çizelge türü" />

      <ErrorNote error={error} />
      {loading ? (
        <PageLoader />
      ) : categories?.length ? (
        <div className="stack" style={{ marginTop: 12 }}>
          {categories.map((cat) => (
            <Card key={cat.id}>
              <div className="row-between row">
                <h3 style={{ margin: 0 }}>{cat.title}</h3>
                <button className="icon-btn" onClick={() => removeCategory(cat)} aria-label="Başlığı sil"><Trash2 size={16} /></button>
              </div>
              {cat.items.length > 0 && (
                <div className="list" style={{ marginTop: 8 }}>
                  {cat.items.map((item) => (
                    <div className="list-item as-row" key={item.id}>
                      <span className="grow">{item.title}</span>
                      <button className="icon-btn" onClick={() => removeItem(item.id)} aria-label="Konuyu sil"><Trash2 size={16} /></button>
                    </div>
                  ))}
                </div>
              )}
              <AddItemRow categoryId={cat.id} onAdded={reload} />
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <Empty title="Henüz başlık yok" text="Önce bir başlık ekle (örn. SEVİYE 1), sonra altına konu ekle." />
        </Card>
      )}

      {creating && (
        <CreateCategorySheet kind={kind} onClose={() => setCreating(false)} onCreated={() => { setCreating(false); toast('Eklendi'); reload() }} />
      )}
    </>
  )
}
