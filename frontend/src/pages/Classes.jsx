import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GraduationCap, Plus } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Sheet, TextField } from '../components/ui.jsx'
import { useToast } from '../components/ui.jsx'

function CreateClassroomSheet({ onClose, onCreated }) {
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const classroom = await api.post('/classes', { name })
      onCreated(classroom)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni sınıf" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <TextField label="Sınıf adı" value={name} onChange={(e) => setName(e.target.value)} placeholder="Örn. Cumartesi Tecvid Grubu" autoFocus required />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Sınıfı oluştur</Button>
      </form>
    </Sheet>
  )
}

export default function Classes() {
  const { data: classes, loading, error, reload } = useLoad(() => api.get('/classes'), [])
  const [creating, setCreating] = useState(false)
  const toast = useToast()

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader
        title="Sınıflarım"
        subtitle="Sınıf oluştur, katılım kodunu paylaş, öğrencilerini takip et."
        actions={<Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>Yeni sınıf</Button>}
      />
      <ErrorNote error={error} />
      {classes?.length ? (
        <div className="grid grid-cards">
          {classes.map((c) => (
            <Card as={Link} to={`/panel/siniflar/${c.id}`} key={c.id} className="stack" style={{ gap: 8 }}>
              <h3>{c.name}</h3>
              <span className="join-code">{c.join_code}</span>
              {!c.join_enabled && <span className="pill pill-warn">Katılım kapalı</span>}
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <Empty icon={GraduationCap} title="Henüz sınıfın yok" text="İlk sınıfını oluştur; öğrencilerin katılım kodu veya linkle katılabilsin." />
        </Card>
      )}
      {creating && (
        <CreateClassroomSheet
          onClose={() => setCreating(false)}
          onCreated={() => { setCreating(false); toast('Sınıf oluşturuldu'); reload() }}
        />
      )}
    </>
  )
}
