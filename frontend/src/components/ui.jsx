import { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import { Check, Loader2, X } from 'lucide-react'
import { errText } from '../i18n/tr'

export function Spinner({ label = 'Yükleniyor' }) {
  return (
    <span className="spinner" role="status" aria-label={label}>
      <Loader2 size={20} />
    </span>
  )
}

export function PageLoader() {
  return (
    <div className="page-loader">
      <Spinner />
    </div>
  )
}

export function Button({ variant = 'secondary', busy, icon: Icon, children, className = '', ...rest }) {
  return (
    <button {...rest} disabled={rest.disabled || busy} className={`btn btn-${variant} ${className}`}>
      {busy ? <Loader2 size={16} className="spin" /> : Icon ? <Icon size={16} aria-hidden="true" /> : null}
      {children}
    </button>
  )
}

export function Pill({ tone = 'neutral', children }) {
  return <span className={`pill pill-${tone}`}>{children}</span>
}

export function Card({ children, className = '', as: Tag = 'div', ...rest }) {
  return <Tag className={`card ${className}`} {...rest}>{children}</Tag>
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <header className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  )
}

export function Empty({ icon: Icon, title, text, action }) {
  return (
    <div className="empty">
      {Icon && <Icon size={32} aria-hidden="true" />}
      <h3>{title}</h3>
      {text && <p className="muted">{text}</p>}
      {action}
    </div>
  )
}

export function ErrorNote({ error }) {
  if (!error) return null
  return (
    <p className="error-note" role="alert">
      {errText(error)}
    </p>
  )
}

/* ---- Form alanları ---- */
export function Field({ label, hint, error, children, id, hideLabel }) {
  const auto = useId()
  const fid = id || auto
  return (
    <div className={`field ${error ? 'has-error' : ''}`}>
      <label htmlFor={fid} className={hideLabel ? 'sr-only' : undefined}>{label}</label>
      {children(fid, error ? `${fid}-err` : undefined)}
      {hint && !error && <small className="muted">{hint}</small>}
      {error && (
        <small id={`${fid}-err`} className="field-error">
          {error}
        </small>
      )}
    </div>
  )
}

export function TextField({ label, hint, error, ...rest }) {
  return (
    <Field label={label} hint={hint} error={error}>
      {(id, err) => <input id={id} aria-invalid={!!err} aria-describedby={err} {...rest} />}
    </Field>
  )
}

export function TextArea({ label, hint, error, rows = 4, hideLabel, ...rest }) {
  return (
    <Field label={label} hint={hint} error={error} hideLabel={hideLabel}>
      {(id, err) => <textarea id={id} rows={rows} aria-invalid={!!err} aria-describedby={err} {...rest} />}
    </Field>
  )
}

export function SelectField({ label, hint, error, options, placeholder, ...rest }) {
  return (
    <Field label={label} hint={hint} error={error}>
      {(id, err) => (
        <select id={id} aria-invalid={!!err} aria-describedby={err} {...rest}>
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      )}
    </Field>
  )
}

export function Segmented({ value, onChange, options, label }) {
  return (
    <div className="segmented" role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          className={value === o.value ? 'on' : ''}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Toggle({ checked, onChange, label, disabled }) {
  return (
    <label className={`toggle ${disabled ? 'disabled' : ''}`}>
      <input type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span className="toggle-track" aria-hidden="true" />
      <span>{label}</span>
    </label>
  )
}

/* ---- Sheet (modal) ---- */
export function Sheet({ title, onClose, children, footer, wide }) {
  const ref = useRef(null)
  useEffect(() => {
    const prev = document.activeElement
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Tab' && ref.current) {
        const f = ref.current.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])')
        const list = [...f].filter((el) => !el.disabled && el.offsetParent !== null)
        if (!list.length) return
        const first = list[0], last = list[list.length - 1]
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    const first = ref.current?.querySelector('input,select,textarea')
    ;(first || ref.current)?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      prev?.focus?.()
    }
  }, [onClose])
  return (
    <div className="scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`sheet ${wide ? 'sheet-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title} ref={ref} tabIndex={-1}>
        <div className="sheet-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Kapat">
            <X size={18} />
          </button>
        </div>
        <div className="sheet-body">{children}</div>
        {footer && <div className="sheet-foot">{footer}</div>}
      </div>
    </div>
  )
}

/* ---- Onay ---- */
const ConfirmContext = createContext(null)
export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null)
  const ask = useCallback((opts) => new Promise((resolve) => setState({ ...opts, resolve })), [])
  const done = (v) => {
    state.resolve(v)
    setState(null)
  }
  return (
    <ConfirmContext.Provider value={ask}>
      {children}
      {state && (
        <Sheet
          title={state.title}
          onClose={() => done(false)}
          footer={
            <>
              <Button onClick={() => done(false)}>Vazgeç</Button>
              <Button variant={state.danger ? 'danger' : 'primary'} onClick={() => done(true)}>
                {state.confirmLabel || 'Onayla'}
              </Button>
            </>
          }
        >
          <p>{state.text}</p>
        </Sheet>
      )}
    </ConfirmContext.Provider>
  )
}
export const useConfirm = () => useContext(ConfirmContext)

/* ---- Toast ---- */
const ToastContext = createContext(null)
export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const push = useCallback((text, tone = 'ok') => {
    const id = Math.random().toString(36).slice(2)
    setItems((x) => [...x, { id, text, tone }])
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 4500)
  }, [])
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {items.map((i) => (
          <div key={i.id} className={`toast toast-${i.tone}`}>
            {i.tone === 'ok' && <Check size={16} aria-hidden="true" />}
            {i.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
export const useToast = () => useContext(ToastContext)
