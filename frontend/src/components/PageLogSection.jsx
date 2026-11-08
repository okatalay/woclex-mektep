import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from './hooks'
import { Button, Card, ErrorNote, PageLoader, TextField, useToast } from './ui.jsx'

export default function PageLogSection({ studentId, editable = false }) {
  const listPath = studentId ? `/students/${studentId}/page-logs` : '/me/page-logs'
  const { data: logs, loading, error, reload } = useLoad(() => api.get(listPath), [listPath])
  const [logDate, setLogDate] = useState('')
  const [startPage, setStartPage] = useState('')
  const [endPage, setEndPage] = useState('')
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState(null)
  const toast = useToast()

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setFormError(null)
    try {
      await api.post(`/students/${studentId}/page-logs`, {
        log_date: logDate, start_page: Number(startPage), end_page: Number(endPage),
      })
      setLogDate(''); setStartPage(''); setEndPage('')
      toast('Kaydedildi')
      reload()
    } catch (err) {
      setFormError(err)
    } finally {
      setBusy(false)
    }
  }

  async function remove(logId) {
    await api.del(`/students/${studentId}/page-logs/${logId}`)
    reload()
  }

  return (
    <Card>
      <h3>Kur'an sayfa takibi</h3>
      {loading ? (
        <PageLoader />
      ) : error ? (
        <ErrorNote error={error} />
      ) : logs.length ? (
        <div className="list">
          {logs.map((l) => (
            <div className="list-item as-row" key={l.id}>
              <div className="grow">
                <strong>{l.start_page}–{l.end_page}. sayfa</strong>
                <div className="muted">{new Date(l.log_date).toLocaleDateString('tr-TR')}{l.note ? ` · ${l.note}` : ''}</div>
              </div>
              {editable && (
                <button type="button" className="icon-btn" onClick={() => remove(l.id)} aria-label="Sil"><Trash2 size={16} /></button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">Henüz kayıt yok.</p>
      )}

      {editable && (
        <form className="row" style={{ marginTop: 12, alignItems: 'flex-end', flexWrap: 'wrap' }} onSubmit={submit}>
          <TextField label="Tarih" type="date" value={logDate} onChange={(e) => setLogDate(e.target.value)} required />
          <TextField label="Başlangıç" type="number" min={1} max={604} value={startPage} onChange={(e) => setStartPage(e.target.value)} required style={{ width: 90 }} />
          <TextField label="Bitiş" type="number" min={1} max={604} value={endPage} onChange={(e) => setEndPage(e.target.value)} required style={{ width: 90 }} />
          <Button variant="primary" busy={busy} type="submit">Ekle</Button>
        </form>
      )}
      <ErrorNote error={formError} />
    </Card>
  )
}
