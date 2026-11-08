import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined) // undefined = yükleniyor, null = giriş yok

  const load = useCallback(async () => {
    try {
      setUser(await api.get('/auth/me'))
    } catch {
      setUser(null)
    }
  }, [])

  useEffect(() => {
    load()
    const expired = () => setUser(null)
    window.addEventListener('auth:expired', expired)
    return () => window.removeEventListener('auth:expired', expired)
  }, [load])

  const value = useMemo(
    () => ({
      user,
      setUser,
      reload: load,
      can: (perm) => !!user?.permissions?.includes(perm),
      roleKey: user?.role?.system_key,
      isInstitution: user?.organization?.type === 'institution',
      async logout() {
        await api.post('/auth/logout')
        setUser(null)
      },
    }),
    [user, load],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
