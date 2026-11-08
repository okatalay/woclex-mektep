import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft, Send } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { ErrorNote, PageHeader, PageLoader } from '../components/ui.jsx'

export default function MessageThread() {
  const { id } = useParams()
  const { data: conversations } = useLoad(() => api.get('/messages/conversations'), [])
  const { data: messages, loading, error, setData } = useLoad(() => api.get(`/messages/conversations/${id}/messages`), [id])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef(null)
  const peer = conversations?.find((c) => c.conversation_id === id)?.peer

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [messages])

  async function send(e) {
    e.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    try {
      const msg = await api.post(`/messages/conversations/${id}/messages`, { body: text.trim() })
      setData((prev) => [...(prev || []), msg])
      setText('')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <PageLoader />
  if (error) return <ErrorNote error={error} />

  return (
    <>
      <Link to="/panel/mesajlar" className="back"><ChevronLeft size={16} aria-hidden="true" />Mesajlar</Link>
      <PageHeader title={peer?.full_name || 'Sohbet'} />

      <div className="chat-thread">
        {messages.map((m) => (
          <div className={`bubble ${m.mine ? 'bubble-mine' : 'bubble-theirs'}`} key={m.id}>
            <p>{m.body}</p>
            <span className="bubble-time">{new Date(m.created_at).toLocaleString('tr-TR', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-row" onSubmit={send}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Mesaj yaz..." aria-label="Mesaj" />
        <button type="submit" className="icon-btn" disabled={busy || !text.trim()} aria-label="Gönder">
          <Send size={18} />
        </button>
      </form>
    </>
  )
}
