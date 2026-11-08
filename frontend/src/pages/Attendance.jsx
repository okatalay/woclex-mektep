import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from '../components/hooks'
import { Button, Card, ErrorNote, PageHeader, PageLoader, Segmented, useToast } from '../components/ui.jsx'

const STATUS_OPTIONS = [
  { value: 'geldi', label: 'Geldi' },
  { value: 'gec_geldi', label: 'Geç' },
  { value: 'izinli', label: 'İzinli' },
  { value: 'gelmedi', label: 'Yok' },
  { value: 'raporlu', label: 'Raporlu' },
]

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export default function Attendance() {
  const { id } = useParams()
  const [date, setDate] = useState(todayISO())
  const { data: rows, loading, error, setData } = useLoad(() => api.get(`/classes/${id}/attendance?date=${date}`), [id, date])
  const { data: summary, reload: reloadSummary } = useLoad(() => api.get(`/classes/${id}/attendance/summary`), [id])
  const [busy, setBusy] = useState(false)
  const toast = useToast()

  function setStatus(studentId, status) {
    setData((rs) => rs.map((r) => (r.student_id === studentId ? { ...r, status } : r)))
  }

  async function save() {
    setBusy(true)
    try {
      await api.post(`/classes/${id}/attendance`, {
        date,
        records: rows.filter((r) => r.status).map((r) => ({ student_id: r.student_id, status: r.status })),
      })
      toast('Yoklama kaydedildi')
      reloadSummary()
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Link to={`/panel/siniflar/${id}`} className="back"><ChevronLeft size={16} aria-hidden="true" />Sınıfa dön</Link>
      <PageHeader
        title="Yoklama"
        subtitle="Tarihi seç, her öğrenci için durumu işaretle."
        actions={<input type="date" value={date} onChange={(e) => setDate(e.target.value)} max={todayISO()} />}
      />

      <Card>
        {loading ? (
          <PageLoader />
        ) : error ? (
          <ErrorNote error={error} />
        ) : rows.length ? (
          <div className="stack">
            {rows.map((r) => (
              <div className="row-between row" key={r.student_id} style={{ flexWrap: 'wrap', gap: 8 }}>
                <strong>{r.full_name}</strong>
                <Segmented
                  value={r.status || ''}
                  onChange={(v) => setStatus(r.student_id, v)}
                  options={STATUS_OPTIONS}
                  label={`${r.full_name} yoklama durumu`}
                />
              </div>
            ))}
            <Button variant="primary" busy={busy} onClick={save} className="btn-block">Kaydet</Button>
          </div>
        ) : (
          <p className="muted">Sınıfta öğrenci yok.</p>
        )}
      </Card>

      {summary?.length > 0 && (
        <Card>
          <h3>Devam özeti</h3>
          <div className="list">
            {summary.map((s) => (
              <div className="list-item as-row" key={s.student_id}>
                <div className="grow">
                  <strong>{s.full_name}</strong>
                  <div className="muted">{s.present}/{s.total} gün</div>
                </div>
                <span className="pill pill-neutral">%{s.rate_pct}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </>
  )
}
