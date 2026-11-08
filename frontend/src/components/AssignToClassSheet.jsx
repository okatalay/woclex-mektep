import { useState } from 'react'
import { api } from '../api/client'
import { useLoad } from './hooks'
import { Button, ErrorNote, SelectField, Sheet, TextField, useToast } from './ui.jsx'
import StudentPicker from './StudentPicker.jsx'

/** `submitLabel` + `onSubmit(classroomId, studentIds, dueAt)` — çağıran taraf isteği yapar. */
export default function AssignToClassSheet({ title, submitLabel, onClose, onAssigned, onSubmit, withDueDate = true }) {
  const { data: classes } = useLoad(() => api.get('/classes'), [])
  const [classroomId, setClassroomId] = useState('')
  const [studentIds, setStudentIds] = useState(null)
  const [dueAt, setDueAt] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const toast = useToast()

  async function submit(e) {
    e.preventDefault()
    if (!classroomId) {
      setError({ code: 'required' })
      return
    }
    if (studentIds !== null && studentIds.length === 0) {
      setError({ code: 'no_valid_students' })
      return
    }
    setBusy(true)
    setError(null)
    try {
      await onSubmit(classroomId, studentIds, dueAt ? new Date(dueAt).toISOString() : null)
      toast('Atandı')
      onAssigned?.()
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <Sheet title={title} onClose={onClose}>
      <form className="stack" onSubmit={submit}>
        <SelectField
          label="Sınıf"
          placeholder="Sınıf seç"
          value={classroomId}
          onChange={(e) => { setClassroomId(e.target.value); setStudentIds(null) }}
          options={(classes || []).map((c) => ({ value: c.id, label: c.name }))}
          required
        />
        {classroomId && <StudentPicker classroomId={classroomId} value={studentIds} onChange={setStudentIds} />}
        {withDueDate && (
          <TextField label="Son teslim tarihi (opsiyonel)" type="date" value={dueAt} onChange={(e) => setDueAt(e.target.value)} />
        )}
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit" className="btn-block">{submitLabel}</Button>
      </form>
    </Sheet>
  )
}
