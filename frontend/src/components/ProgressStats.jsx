export default function ProgressStats({ progress }) {
  if (!progress) return null
  const { assigned, submitted, reviewed, redo_requested, avg_score, completion_rate } = progress
  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="row-between row">
        <span className="muted" style={{ fontSize: '0.87rem' }}>Tamamlanma</span>
        <strong>%{completion_rate}</strong>
      </div>
      <div className="progress-bar" role="progressbar" aria-valuenow={completion_rate} aria-valuemin={0} aria-valuemax={100}>
        <div className="progress-bar-fill" style={{ width: `${completion_rate}%` }} />
      </div>
      <div className="tracking-grid">
        <div className="stat">
          <span className="stat-value">{assigned}</span>
          <span className="stat-label">Atanan</span>
        </div>
        <div className="stat">
          <span className="stat-value">{submitted}</span>
          <span className="stat-label">Teslim edilen</span>
        </div>
        <div className="stat">
          <span className="stat-value">{reviewed}</span>
          <span className="stat-label">İncelenen</span>
        </div>
        <div className="stat">
          <span className="stat-value">{avg_score ?? '—'}</span>
          <span className="stat-label">Ortalama puan</span>
        </div>
      </div>
      {redo_requested > 0 && <span className="pill pill-warn">{redo_requested} ödev tekrar isteniyor</span>}
    </div>
  )
}
