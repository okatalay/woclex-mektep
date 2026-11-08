import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { BookOpen, ChevronLeft, ChevronRight, Copy, Megaphone, Plus, RefreshCw, Route as RouteIcon, Users } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, Empty, ErrorNote, PageHeader, PageLoader, Pill, Sheet, TextArea, TextField, Toggle, useToast } from '../components/ui.jsx'
import CreateAssignmentSheet from '../components/CreateAssignmentSheet.jsx'
import StudentPicker from '../components/StudentPicker.jsx'

function CreateRouteSheet({ classroomId, onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [studentIds, setStudentIds] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    if (studentIds !== null && studentIds.length === 0) {
      setError({ code: 'no_valid_students' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      const r = await api.post(`/classes/${classroomId}/routes`, { title, description: description || null, student_ids: studentIds })
      onCreated(r)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni rota" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <TextField label="Rota adı" value={title} onChange={(e) => setTitle(e.target.value)}
          placeholder="Örn. Tecvid Yolculuğu" autoFocus required minLength={2} />
        <TextArea label="Açıklama (opsiyonel)" value={description} onChange={(e) => setDescription(e.target.value)}
          placeholder="Bu rotanın amacı ne?" />
        <StudentPicker classroomId={classroomId} value={studentIds} onChange={setStudentIds} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Rotayı oluştur</Button>
      </form>
    </Sheet>
  )
}

function CreateAnnouncementSheet({ classroomId, onClose, onCreated }) {
  const [body, setBody] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const a = await api.post(`/classes/${classroomId}/announcements`, { body })
      onCreated(a)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title="Yeni duyuru" onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <TextArea label="Duyuru metni" value={body} onChange={(e) => setBody(e.target.value)}
          placeholder="Örn. Bu cumartesi ders saat 10'da başlayacak." autoFocus required minLength={1} />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">Duyuruyu yayınla</Button>
      </form>
    </Sheet>
  )
}

function assignmentTone(a) {
  if (a.target_count > 0 && a.reviewed_count === a.target_count) return 'ok'
  if (a.submitted_count > 0) return 'accent'
  return 'neutral'
}

function whatsappMessage(c) {
  return [
    'Merhaba! 📖 Sınıfımız açıldı.',
    '',
    `Katılmak için aşağıdaki bağlantıya dokunun; kayıt kodumuz kendiliğinden yazılır:`,
    c.join_url,
    '',
    `Kayıt kodumuz: ${c.join_code}`,
  ].join('\n')
}

export default function ClassDetail() {
  const { id } = useParams()
  const { data: classroom, loading, error, reload } = useLoad(() => api.get(`/classes/${id}`), [id])
  const { data: students } = useLoad(() => api.get(`/classes/${id}/students`), [id])
  const { data: assignments, reload: reloadAssignments } = useLoad(() => api.get(`/classes/${id}/assignments`), [id])
  const { data: announcements, reload: reloadAnnouncements } = useLoad(() => api.get(`/classes/${id}/announcements`), [id])
  const { data: routes, reload: reloadRoutes } = useLoad(() => api.get(`/classes/${id}/routes`), [id])
  const [busy, setBusy] = useState(false)
  const [creatingAssignment, setCreatingAssignment] = useState(false)
  const [creatingAnnouncement, setCreatingAnnouncement] = useState(false)
  const [creatingRoute, setCreatingRoute] = useState(false)
  const toast = useToast()

  if (loading) return <PageLoader />
  if (error || !classroom) return <ErrorNote error={error} />

  function copy(text) {
    navigator.clipboard?.writeText(text)
    toast('Kopyalandı')
  }

  async function toggleJoin(v) {
    setBusy(true)
    try {
      await api.patch(`/classes/${id}`, { join_enabled: v })
      reload()
    } finally {
      setBusy(false)
    }
  }

  async function regenerate() {
    setBusy(true)
    try {
      await api.post(`/classes/${id}/regenerate-code`)
      toast('Kod yenilendi')
      reload()
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Link to="/panel/siniflar" className="back"><ChevronLeft size={16} aria-hidden="true" />Sınıflarım</Link>
      <PageHeader title={classroom.name} subtitle="Katılım kodu, davet linki ve öğrenci listesi." />

      <Card className="stack">
        <div className="row-between row">
          <div>
            <small className="muted">ÖĞRENCİ KAYIT KODU</small>
            <div className="join-code">{classroom.join_code}</div>
          </div>
          <Toggle checked={classroom.join_enabled} onChange={toggleJoin} label="Katılım açık" disabled={busy} />
        </div>
        <div className="row">
          <Button icon={Copy} onClick={() => copy(classroom.join_code)}>Kodu kopyala</Button>
          <Button icon={Copy} onClick={() => copy(classroom.join_url)}>Linki kopyala</Button>
          <a className="btn btn-secondary" href={`https://wa.me/?text=${encodeURIComponent(whatsappMessage(classroom))}`} target="_blank" rel="noreferrer">
            WhatsApp'ta paylaş
          </a>
          <Button icon={RefreshCw} busy={busy} onClick={regenerate}>Kodu yenile</Button>
        </div>
        <p className="copy-line">{classroom.join_url}</p>
      </Card>

      <Card>
        <div className="row-between row">
          <h3>Rotalar</h3>
          <Button variant="primary" icon={Plus} onClick={() => setCreatingRoute(true)}>Yeni rota</Button>
        </div>
        {routes?.length ? (
          <div className="list">
            {routes.map((r) => (
              <Link className="list-item" to={`/panel/siniflar/${id}/rotalar/${r.id}`} key={r.id}>
                <div className="grow">
                  <strong>{r.title}</strong>
                  <div className="muted">{r.stop_count} durak</div>
                </div>
                <ChevronRight size={18} aria-hidden="true" className="muted" />
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={RouteIcon} title="Henüz rota yok" text="Öğrencinin adım adım ilerleyeceği bir yolculuk oluştur." />
        )}
      </Card>

      <Card>
        <div className="row-between row">
          <h3>Ödevler</h3>
          <Button variant="primary" icon={Plus} onClick={() => setCreatingAssignment(true)}>Yeni ödev</Button>
        </div>
        {assignments?.length ? (
          <div className="list">
            {assignments.map((a) => (
              <Link className="list-item" to={`/panel/siniflar/${id}/odevler/${a.id}`} key={a.id}>
                <div className="grow">
                  <strong>{a.title}</strong>
                  <div className="muted">
                    {a.submitted_count}/{a.target_count} teslim
                    {a.due_at ? ` · Son tarih ${new Date(a.due_at).toLocaleDateString('tr-TR')}` : ''}
                  </div>
                </div>
                <Pill tone={assignmentTone(a)}>{a.reviewed_count}/{a.target_count} incelendi</Pill>
                <ChevronRight size={18} aria-hidden="true" className="muted" />
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={BookOpen} title="Henüz ödev yok" text="Sınıfa ilk ödevini ata." />
        )}
      </Card>

      <Card>
        <div className="row-between row">
          <h3>Duyurular</h3>
          <Button icon={Plus} onClick={() => setCreatingAnnouncement(true)}>Duyuru yap</Button>
        </div>
        {announcements?.length ? (
          <div className="stack">
            {announcements.map((a) => (
              <div className="list-item" style={{ display: 'block' }} key={a.id}>
                <div className="muted">{new Date(a.created_at).toLocaleDateString('tr-TR')}</div>
                <p style={{ margin: '4px 0 0' }}>{a.body}</p>
              </div>
            ))}
          </div>
        ) : (
          <Empty icon={Megaphone} title="Henüz duyuru yok" text="Öğrenci ve velilere bir duyuru paylaş." />
        )}
      </Card>

      <Card>
        <h3>Öğrenciler</h3>
        {students?.length ? (
          <div className="list">
            {students.map((s) => (
              <Link className="list-item" to={`/panel/siniflar/${id}/ogrenciler/${s.student_id}`} key={s.student_id}>
                <div className="grow">
                  <strong>{s.full_name}</strong>
                  <div className="muted">@{s.username}</div>
                </div>
                <ChevronRight size={18} aria-hidden="true" className="muted" />
              </Link>
            ))}
          </div>
        ) : (
          <Empty icon={Users} title="Henüz öğrenci yok" text="Katılım kodunu veya linkini öğrencilerinle paylaş." />
        )}
      </Card>

      {creatingAssignment && (
        <CreateAssignmentSheet
          classroomId={id}
          onClose={() => setCreatingAssignment(false)}
          onCreated={() => { setCreatingAssignment(false); reloadAssignments() }}
        />
      )}
      {creatingAnnouncement && (
        <CreateAnnouncementSheet
          classroomId={id}
          onClose={() => setCreatingAnnouncement(false)}
          onCreated={() => { setCreatingAnnouncement(false); toast('Duyuru yayınlandı'); reloadAnnouncements() }}
        />
      )}
      {creatingRoute && (
        <CreateRouteSheet
          classroomId={id}
          onClose={() => setCreatingRoute(false)}
          onCreated={() => { setCreatingRoute(false); toast('Rota oluşturuldu'); reloadRoutes() }}
        />
      )}
    </>
  )
}
