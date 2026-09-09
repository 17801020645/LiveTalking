export async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
    const err = new Error(body.msg || `HTTP ${res.status}`)
    err.status = res.status
    err.body = body
    throw err
  }
  return body.data
}
