import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MessageCircle, Plus } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Pill, Sheet } from '../components/ui.jsx'

function NewMessageSheet({ onClose }) {
  const { data: contacts, loading, error } = useLoad(() => api.get('/messages/contacts'), [])
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function start(peer) {
    setBusy(true)
    try {
      const { conversation_id } = await api.post('/messages/conversations', { peer_user_id: peer.user_id })
      onClose()
      nav(`/panel/mesajlar/${conversation_id}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni mesaj" onClose={onClose}>
      {loading ? (
        <PageLoader />
      ) : error ? (
        <ErrorNote error={error} />
      ) : contacts.length ? (
        <div className="list">
          {contacts.map((c) => (
            <button className="list-item as-row" key={c.user_id} disabled={busy} onClick={() => start(c)}>
              <div className="grow">
                <strong>{c.full_name}</strong>
                <div className="muted">{c.context}</div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <Empty title="Kimse yok" text="Mesajlaşabileceğin biri henüz bağlı değil." />
      )}
    </Sheet>
  )
}

export default function Messages() {
  const { data: conversations, loading, error } = useLoad(() => api.get('/messages/conversations'), [])
  const [creating, setCreating] = useState(false)

  if (loading) return <PageLoader />

  return (
    <>
      <PageHeader
        title="Mesajlar"
        actions={<Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>Yeni mesaj</Button>}
      />
      <ErrorNote error={error} />
      <Card>
        {conversations?.length ? (
          <div className="list">
            {conversations.map((c) => (
              <Link className="list-item" to={`/panel/mesajlar/${c.conversation_id}`} key={c.conversation_id}>
                <div className="grow">
                  <strong>{c.peer.full_name}</strong>
                  <div className="muted">{c.last_message || 'Henüz mesaj yok'}</div>
                </div>
                {c.unread_count > 0 && <Pill tone="accent">{c.unread_count}</Pill>}
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={MessageCircle} title="Henüz mesajın yok" text="Yeni mesaj başlat." />
        )}
      </Card>
      {creating && <NewMessageSheet onClose={() => setCreating(false)} />}
    </>
  )
}
