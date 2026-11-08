import { useCallback, useEffect, useState } from 'react'

/** Basit veri çekme: { data, error, loading, reload, setData } */
export function useLoad(fn, deps = []) {
  const [state, setState] = useState({ data: undefined, error: null, loading: true })
  const run = useCallback(async () => {
    try {
      const data = await fn()
      setState({ data, error: null, loading: false })
    } catch (error) {
      setState((s) => ({ ...s, error, loading: false }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    setState((s) => ({ ...s, loading: true }))
    run()
  }, [run])
  return {
    ...state,
    reload: run,
    setData: (data) => setState((s) => ({ ...s, data: typeof data === 'function' ? data(s.data) : data })),
  }
}
