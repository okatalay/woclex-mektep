import { Award, BookOpen, CalendarCheck } from 'lucide-react'

export default function TrackingSummary({ summary }) {
  if (!summary) return null
  const { ezber, tecvid, pages, attendance, badge } = summary
  return (
    <div className="stack" style={{ gap: 12 }}>
      {badge && (
        <div className="row" style={{ gap: 8, alignItems: 'center' }}>
          <Award size={20} className="star-on" aria-hidden="true" />
          <strong>{badge}</strong>
        </div>
      )}
      <div className="tracking-grid">
        <div className="stat">
          <span className="stat-value">%{ezber.pct}</span>
          <span className="stat-label">Ezber ({ezber.completed}/{ezber.total})</span>
        </div>
        <div className="stat">
          <span className="stat-value">%{tecvid.pct}</span>
          <span className="stat-label">Tecvid ({tecvid.completed}/{tecvid.total})</span>
        </div>
        <div className="stat">
          <span className="stat-value">{pages.current_page ?? '—'}</span>
          <span className="stat-label"><BookOpen size={12} aria-hidden="true" /> Kaldığı sayfa</span>
        </div>
        <div className="stat">
          <span className="stat-value">%{attendance.rate_pct}</span>
          <span className="stat-label"><CalendarCheck size={12} aria-hidden="true" /> Devam oranı</span>
        </div>
      </div>
    </div>
  )
}
