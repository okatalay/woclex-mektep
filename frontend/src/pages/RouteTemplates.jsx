import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Plus, Route as RouteIcon } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Sheet, TextArea, TextField, useToast } from '../components/ui.jsx'

function CreateTemplateSheet({ onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const t = await api.post('/route-templates', { title, description: description || null })
      onCreated(t)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni rota şablonu" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <TextField label="Şablon adı" value={title} onChange={(e) => setTitle(e.target.value)}
          placeholder="Örn. Tecvid Yolculuğu" autoFocus required minLength={2} />
        <TextArea label="Açıklama (opsiyonel)" value={description} onChange={(e) => setDescription(e.target.value)} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Şablonu oluştur</Button>
      </form>
    </Sheet>
  )
}

export default function RouteTemplates() {
  const { data: templates, loading, error, reload } = useLoad(() => api.get('/route-templates'), [])
  const [creating, setCreating] = useState(false)
  const toast = useToast()

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader
        title="Rota"
        subtitle="Yeniden kullanılabilir yolculuk şablonları; tek tıkla sınıfa veya seçili öğrencilere uygula."
        actions={<Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>Yeni şablon</Button>}
      />
      <ErrorNote error={error} />
      {templates?.length ? (
        <div className="list">
          {templates.map((t) => (
            <Link className="list-item" to={`/panel/rota-arsivi/${t.id}`} key={t.id}>
              <div className="grow">
                <strong>{t.title}</strong>
                <div className="muted">{t.stop_count} durak</div>
              </div>
              <ChevronRight size={18} aria-hidden="true" className="muted" />
            </Link>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={RouteIcon} title="Şablon yok" text="Sık kullandığın yolculukları şablon yap; her sınıfta yeniden kurma." />
        </Card>
      )}
      {creating && (
        <CreateTemplateSheet
          onClose={() => setCreating(false)}
          onCreated={() => { setCreating(false); toast('Şablon oluşturuldu'); reload() }}
        />
      )}
    </>
  )
}
