import { api } from '../api/client'
import { useLoad } from './hooks'
import { Segmented } from './ui.jsx'

/** value: null = tüm sınıf, string[] = seçili öğrenci id'leri. */
export default function StudentPicker({ classroomId, value, onChange }) {
  const { data: students } = useLoad(() => api.get(`/classes/${classroomId}/students`), [classroomId])
  const mode = value === null ? 'class' : 'students'

  function toggle(id) {
    const cur = value || []
    onChange(cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id])
  }

  return (
    <div className="field">
      <label>Kime atanacak</label>
      <Segmented
        value={mode}
        onChange={(m) => onChange(m === 'class' ? null : [])}
        options={[{ value: 'class', label: 'Tüm sınıf' }, { value: 'students', label: 'Seçili öğrenciler' }]}
      />
      {mode === 'students' && (
        <div className="student-picker-list">
          {students?.length ? (
            students.map((s) => (
              <label key={s.student_id} className={`type-chip ${(value || []).includes(s.student_id) ? 'on' : ''}`}>
                <input type="checkbox" checked={(value || []).includes(s.student_id)} onChange={() => toggle(s.student_id)} />
                {s.full_name}
              </label>
            ))
          ) : (
            <small className="muted">Sınıfta öğrenci yok.</small>
          )}
        </div>
      )}
    </div>
  )
}
