import { api } from '../api/client'
import { useLoad } from './hooks'
import { Card, Empty, ErrorNote, PageLoader } from './ui.jsx'
import { BookMarked } from 'lucide-react'

const STATUS_CYCLE = ['-', 'calisiyor', 'tekrar', 'ezberlendi']
const STATUS_LABEL = { '-': 'Başlamadı', calisiyor: 'Çalışıyor', tekrar: 'Tekrar', ezberlendi: 'Ezberlendi' }
const STATUS_TONE = { '-': 'neutral', calisiyor: 'accent', tekrar: 'warn', ezberlendi: 'ok' }

/**
 * `endpoint`: veriyi getirecek yol (`/curriculum?kind=X&student_id=Y`, `/me/curriculum?kind=X`,
 * `/guardians/children/{id}/curriculum?kind=X`). `editable` true ise (yalnız eğitmen) satıra
 * tıklayınca durum döngüsel ilerler ve `/curriculum/items/{id}/status` ile kaydedilir.
 */
export default function CurriculumChart({ endpoint, studentId, editable = false }) {
  const { data, loading, error, setData } = useLoad(() => api.get(endpoint), [endpoint])

  if (loading) return <PageLoader />
  if (error) return <ErrorNote error={error} />
  if (!data?.categories?.length) {
    return <Empty icon={BookMarked} title="Henüz konu yok" text={editable ? 'Müfredat sayfasından konu ekle.' : 'Eğitmenin henüz konu eklemesi bekleniyor.'} />
  }

  async function cycle(item) {
    if (!editable) return
    const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(item.status) + 1) % STATUS_CYCLE.length]
    setData((d) => ({
      ...d,
      categories: d.categories.map((c) => ({
        ...c,
        items: c.items.map((i) => (i.id === item.id ? { ...i, status: next } : i)),
      })),
    }))
    await api.post(`/curriculum/items/${item.id}/status`, { student_id: studentId, status: next })
  }

  return (
    <div className="stack">
      {data.categories.map((cat) => (
        <Card key={cat.id}>
          <h4 style={{ margin: '0 0 8px' }}>{cat.title}</h4>
          <div className="list">
            {cat.items.map((item) => (
              <button
                key={item.id}
                className={`list-item as-row curriculum-row ${editable ? 'clickable' : ''}`}
                type="button"
                disabled={!editable}
                onClick={() => cycle(item)}
              >
                <span className="grow">{item.title}</span>
                <span className={`pill pill-${STATUS_TONE[item.status]}`}>{STATUS_LABEL[item.status]}</span>
              </button>
            ))}
          </div>
        </Card>
      ))}
    </div>
  )
}
