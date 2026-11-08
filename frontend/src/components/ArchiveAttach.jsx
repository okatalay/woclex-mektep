import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, Search, X } from 'lucide-react'
import { api } from '../api/client'
import { useLoad } from './hooks'

/** Arşivden aranabilir liste ile seçim; seçilenlerin dosyaları kaydedilince kopyalanır. */
export default function ArchiveAttach({ value, onChange }) {
  const { data: items } = useLoad(() => api.get('/library?kind=arsiv'), [])
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)

  const selected = (items || []).filter((i) => value.includes(i.id))
  const q = query.trim().toLocaleLowerCase('tr')
  const matches = (items || []).filter((i) => !q || i.title.toLocaleLowerCase('tr').includes(q))

  function toggle(id) {
    onChange(value.includes(id) ? value.filter((x) => x !== id) : [...value, id])
  }

  return (
    <div className="field">
      <label>Arşivden ekle (opsiyonel)</label>
      {items && !items.length ? (
        <p className="muted">Arşivin boş. <Link to="/panel/arsiv">Arşive içerik ekle</Link></p>
      ) : (
        <div className="combo" onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false) }}>
          {selected.length > 0 && (
            <div className="row combo-chips">
              {selected.map((i) => (
                <span key={i.id} className="type-chip on">
                  {i.title}
                  <button type="button" className="combo-x" onClick={() => toggle(i.id)} aria-label={`${i.title} kaldır`}><X size={13} /></button>
                </span>
              ))}
            </div>
          )}
          <div className="combo-input">
            <Search size={16} aria-hidden="true" />
            <input
              type="text"
              value={query}
              placeholder="Arşivde ara ve seç..."
              onFocus={() => setOpen(true)}
              onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
              onKeyDown={(e) => { if (e.key === 'Enter') e.preventDefault() }}
              role="combobox"
              aria-expanded={open}
            />
          </div>
          {open && (
            <div className="archive-list" role="listbox" aria-multiselectable="true">
              {matches.length ? matches.map((i) => (
                <button
                  type="button" key={i.id} role="option" aria-selected={value.includes(i.id)}
                  className={`archive-row ${value.includes(i.id) ? 'on' : ''}`}
                  onClick={() => toggle(i.id)}
                >
                  <span className="grow">{i.title}</span>
                  {value.includes(i.id) && <Check size={16} aria-hidden="true" />}
                </button>
              )) : <div className="archive-row muted">Sonuç yok</div>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
