import { useState } from 'react'
import { Copy } from 'lucide-react'
import { api } from '../api/client'
import { Button, ErrorNote, Sheet, useToast } from './ui.jsx'

export default function GuardianInviteSheet({ classroomId, student, onClose }) {
  const [invite, setInvite] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const toast = useToast()

  async function create() {
    setBusy(true)
    setError(null)
    try {
      setInvite(await api.post(`/classes/${classroomId}/students/${student.student_id}/guardian-invite`, {}))
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  function copy(text) {
    navigator.clipboard?.writeText(text)
    toast('Kopyalandı')
  }

  return (
    <Sheet title={`${student.full_name} için veli daveti`} onClose={onClose}>
      <div className="stack">
        {!invite ? (
          <>
            <p className="muted">7 gün geçerli, tek kullanımlık bir davet linki oluşturulur.</p>
            <ErrorNote error={error} />
            <Button variant="primary" busy={busy} onClick={create}>Davet linki oluştur</Button>
          </>
        ) : (
          <>
            <p className="copy-line">{invite.invite_url}</p>
            <Button icon={Copy} onClick={() => copy(invite.invite_url)}>Linki kopyala</Button>
            <a className="btn btn-secondary" href={`https://wa.me/?text=${encodeURIComponent(invite.invite_url)}`} target="_blank" rel="noreferrer">
              WhatsApp'ta paylaş
            </a>
          </>
        )}
      </div>
    </Sheet>
  )
}
