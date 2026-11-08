import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { BookOpen } from 'lucide-react'
import { api } from '../api/client'
import { errText } from '../i18n/tr'
import { useAuth } from '../components/auth.jsx'
import { Button, Card, ErrorNote, PageLoader, TextField } from '../components/ui.jsx'

function AuthShell({ title, subtitle, children, foot, sideTitle, sideText }) {
  return (
    <div className="auth-screen">
      <div className="auth-mobile-brand">
        <span className="brand-mark"><BookOpen size={16} aria-hidden="true" /></span>
        Mektep
      </div>
      <aside className="auth-side">
        <div className="auth-brand">
          <span className="brand-mark"><BookOpen size={16} aria-hidden="true" /></span>
          Mektep
        </div>
        <div className="auth-verse">
          <p className="auth-verse-ar" lang="ar" dir="rtl">اقرأ باسم ربك الذي خلق</p>
          <span className="auth-verse-rule" aria-hidden="true" />
          <p className="auth-verse-tr">“Yaratan Rabbinin adıyla oku.”</p>
          <span className="auth-verse-ref">Alak sûresi, 1. ayet</span>
        </div>
        <div className="auth-side-context">
          <strong>{sideTitle}</strong>
          <p>{sideText}</p>
        </div>
      </aside>
      <div className="auth-panel">
        <Card className="auth-card">
          <div>
            <h1>{title}</h1>
            {subtitle && <p className="muted">{subtitle}</p>}
          </div>
          {children}
          {foot && <p className="auth-alt">{foot}</p>}
        </Card>
      </div>
    </div>
  )
}

export function Login() {
  const { setUser } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      setUser(await api.post('/auth/login', form))
      nav('/panel', { replace: true })
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  return (
    <AuthShell
      title="Giriş yap"
      sideTitle="Ezber ve tilavet yolculuğunu birlikte takip edin"
      sideText="Eğitmen, öğrenci ve veli aynı panelde: ödevler, geri bildirim ve gelişim tek yerde."
      foot={<>Eğitmen olarak hesabın yok mu? <Link to="/kayit">Kayıt ol</Link></>}
    >
      <form className="stack" onSubmit={submit}>
        <TextField label="Kullanıcı adı" value={form.username} onChange={set('username')} autoComplete="username" autoCapitalize="none" autoFocus required />
        <TextField label="Şifre" type="password" value={form.password} onChange={set('password')} autoComplete="current-password" required />
        <ErrorNote error={error} />
        <Button variant="primary" busy={busy} type="submit">Giriş yap</Button>
      </form>
      <p className="auth-alt">
        Öğrenci misin? <Link to="/katil">Sınıf koduyla katıl</Link>
      </p>
    </AuthShell>
  )
}

export function JoinCodeEntry() {
  const nav = useNavigate()
  const [code, setCode] = useState('')
  return (
    <AuthShell
      title="Sınıf koduyla katıl"
      sideTitle="Kod elinde mi?"
      sideText="Eğitmenin sana bir katılım kodu ya da link paylaşmış olmalı."
    >
      <form className="stack" onSubmit={(e) => { e.preventDefault(); nav(`/katil/${code.trim()}`) }}>
        <TextField label="Katılım kodu" value={code} onChange={(e) => setCode(e.target.value)} placeholder="ÖRN. 7K4Q-M2XZ" autoCapitalize="characters" autoFocus required />
        <Button variant="primary" type="submit">Devam et</Button>
      </form>
      <p className="auth-alt">Zaten hesabın var mı? <Link to="/giris">Giriş yap</Link></p>
    </AuthShell>
  )
}

export function RegisterTeacher() {
  const { setUser } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ account_type: 'individual', full_name: '', organization_name: '', username: '', password: '', email: '', phone: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const institution = form.account_type === 'institution'

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    const body = { ...form, email: form.email || null, phone: form.phone || null, organization_name: institution ? form.organization_name : null }
    try {
      setUser(await api.post('/auth/register', body))
      nav('/panel', { replace: true })
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }
  const fe = (k) => (error?.fields?.[k] ? errText(error, k) : undefined)

  return (
    <AuthShell
      title="Eğitmen hesabı oluştur"
      sideTitle="Kurumun mu var, tek başına mı çalışıyorsun?"
      sideText="Bireysel başla, istersen sonra kurum yapısına ve diğer eğitmenlere genişlet."
      foot={<>Zaten hesabın var mı? <Link to="/giris">Giriş yap</Link></>}
    >
      <form className="stack" onSubmit={submit}>
        <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="sr-only">Hesap türü</legend>
          <div className="type-pick">
            <label>
              <input type="radio" name="type" checked={!institution} onChange={() => setForm((f) => ({ ...f, account_type: 'individual' }))} />
              <strong>Bireysel eğitmen</strong>
              <span>Kendi sınıflarımı yönetirim</span>
            </label>
            <label>
              <input type="radio" name="type" checked={institution} onChange={() => setForm((f) => ({ ...f, account_type: 'institution' }))} />
              <strong>Kurum</strong>
              <span>Birden çok eğitmen olacak</span>
            </label>
          </div>
        </fieldset>
        {institution && <TextField label="Kurum adı" value={form.organization_name} onChange={set('organization_name')} error={fe('organization_name')} required />}
        <TextField label="Ad soyad" value={form.full_name} onChange={set('full_name')} error={fe('full_name')} autoComplete="name" required />
        <TextField label="Kullanıcı adı" value={form.username} onChange={set('username')} error={fe('username')} hint="Küçük harf, rakam, nokta, tire veya alt çizgi" autoComplete="username" autoCapitalize="none" required />
        <TextField label="Şifre" type="password" value={form.password} onChange={set('password')} error={fe('password')} hint="En az 8 karakter" autoComplete="new-password" required minLength={8} />
        <div className="form-grid">
          <TextField label="E-posta (isteğe bağlı)" type="email" value={form.email} onChange={set('email')} autoComplete="email" />
          <TextField label="Telefon (isteğe bağlı)" type="tel" value={form.phone} onChange={set('phone')} autoComplete="tel" />
        </div>
        {error && !Object.keys(error.fields).length && <ErrorNote error={error} />}
        <Button variant="primary" busy={busy} type="submit">Hesap oluştur</Button>
      </form>
    </AuthShell>
  )
}

export function JoinStudent() {
  const { setUser } = useAuth()
  const nav = useNavigate()
  const { code } = useParams()
  const [info, setInfo] = useState(undefined)
  const [form, setForm] = useState({ full_name: '', username: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  useEffect(() => {
    api.get(`/auth/join-info/${code}`).then(setInfo).catch((err) => setInfo(null) || setError(err))
  }, [code])

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      setUser(await api.post('/auth/register-student', { ...form, join_code: code }))
      nav('/panel', { replace: true })
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }
  const fe = (k) => (error?.fields?.[k] ? errText(error, k) : undefined)

  if (info === undefined) return <PageLoader />

  return (
    <AuthShell
      title={info ? 'Sınıfa katıl' : 'Kod geçersiz'}
      subtitle={info ? `${info.teacher_name} — ${info.classroom_name} sınıfına katılıyorsun.` : 'Bu katılım kodu artık geçerli değil.'}
      sideTitle="Hoş geldin"
      sideText="Ödevlerini burada teslim edecek, gelişimini burada göreceksin."
      foot={<>Zaten hesabın var mı? <Link to="/giris">Giriş yap</Link></>}
    >
      {info ? (
        <form className="stack" onSubmit={submit}>
          <TextField label="Ad soyad" value={form.full_name} onChange={set('full_name')} error={fe('full_name')} autoComplete="name" required />
          <TextField label="Kullanıcı adı" value={form.username} onChange={set('username')} error={fe('username')} hint="Küçük harf, rakam, nokta, tire veya alt çizgi" autoComplete="username" autoCapitalize="none" required />
          <TextField label="Şifre" type="password" value={form.password} onChange={set('password')} error={fe('password')} hint="En az 8 karakter" autoComplete="new-password" required minLength={8} />
          {error && !Object.keys(error.fields).length && <ErrorNote error={error} />}
          <Button variant="primary" busy={busy} type="submit">Sınıfa katıl</Button>
        </form>
      ) : (
        <ErrorNote error={error} />
      )}
    </AuthShell>
  )
}

export function JoinGuardian() {
  const { setUser } = useAuth()
  const nav = useNavigate()
  const { token } = useParams()
  const [info, setInfo] = useState(undefined)
  const [form, setForm] = useState({ full_name: '', username: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  useEffect(() => {
    api.get(`/auth/guardian-invite/${token}`).then(setInfo).catch((err) => setInfo(null) || setError(err))
  }, [token])

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      setUser(await api.post('/auth/register-guardian', { ...form, token }))
      nav('/panel', { replace: true })
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }
  const fe = (k) => (error?.fields?.[k] ? errText(error, k) : undefined)

  if (info === undefined) return <PageLoader />

  return (
    <AuthShell
      title={info ? 'Veli hesabı oluştur' : 'Davet geçersiz'}
      subtitle={info ? `${info.student_name} için veli hesabı açıyorsun.` : 'Bu davet linki artık geçerli değil.'}
      sideTitle="Gelişimini takip et"
      sideText="Çocuğunun ödevlerini, teslimlerini ve eğitmen geri bildirimini burada görürsün."
      foot={<>Zaten hesabın var mı? <Link to="/giris">Giriş yap</Link></>}
    >
      {info ? (
        <form className="stack" onSubmit={submit}>
          <TextField label="Ad soyad" value={form.full_name} onChange={set('full_name')} error={fe('full_name')} autoComplete="name" required />
          <TextField label="Kullanıcı adı" value={form.username} onChange={set('username')} error={fe('username')} hint="Küçük harf, rakam, nokta, tire veya alt çizgi" autoComplete="username" autoCapitalize="none" required />
          <TextField label="Şifre" type="password" value={form.password} onChange={set('password')} error={fe('password')} hint="En az 8 karakter" autoComplete="new-password" required minLength={8} />
          {error && !Object.keys(error.fields).length && <ErrorNote error={error} />}
          <Button variant="primary" busy={busy} type="submit">Hesap oluştur</Button>
        </form>
      ) : (
        <ErrorNote error={error} />
      )}
    </AuthShell>
  )
}
