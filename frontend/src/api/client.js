export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : detail?.message || 'error')
    this.status = status
    this.detail = detail
    this.code = typeof detail === 'string' ? detail : detail?.code || null
    this.retryAfter = detail?.retry_after || null
    this.fields = {}
    if (Array.isArray(detail)) {
      for (const d of detail) {
        const key = d.loc?.[d.loc.length - 1]
        if (key !== undefined && key !== 'body') this.fields[key] = d.type || 'invalid'
      }
    } else if (detail && typeof detail === 'object' && !detail.code) {
      this.fields = detail
    }
  }
}

async function request(method, path, body, isForm) {
  const opts = { method, credentials: 'same-origin', headers: {} }
  if (body !== undefined) {
    if (isForm) opts.body = body
    else {
      opts.headers['Content-Type'] = 'application/json'
      opts.body = JSON.stringify(body)
    }
  }
  let res
  try {
    res = await fetch('/api' + path, opts)
  } catch {
    throw new ApiError(0, 'network')
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* boş gövde */
  }
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event('auth:expired'))
    throw new ApiError(res.status, data?.detail ?? 'error')
  }
  return data
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b) => request('POST', p, b ?? {}),
  put: (p, b) => request('PUT', p, b ?? {}),
  patch: (p, b) => request('PATCH', p, b ?? {}),
  del: (p) => request('DELETE', p),
  upload: (p, formData) => request('POST', p, formData, true),
}

export const media = (id, size = 'thumb') => `/api/media/${id}?size=${size}`
