const API_BASE = '/api'

export class ProgressApiError extends Error {
  constructor(message, code) {
    super(message)
    this.name = 'ProgressApiError'
    this.code = code
  }
}

async function fetchJson(url) {
  let response

  try {
    response = await fetch(url)
  } catch {
    throw new ProgressApiError(
      'Could not connect to the backend.',
      'unavailable'
    )
  }

  if (response.status === 404) {
    throw new ProgressApiError('Student not found.', 'not-found')
  }

  if (!response.ok) {
    throw new ProgressApiError(
      'Something went wrong while loading progress.',
      'request-failed'
    )
  }

  try {
    return await response.json()
  } catch {
    throw new ProgressApiError(
      'The backend returned an unexpected progress response.',
      'invalid-response'
    )
  }
}

export async function loadProgressSummary(studentId) {
  const data = await fetchJson(
    `${API_BASE}/progress/${encodeURIComponent(studentId)}/summary`
  )

  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new ProgressApiError(
      'The backend returned an unexpected progress response.',
      'invalid-response'
    )
  }

  return data
}

export async function loadProgressRecords(studentId) {
  const data = await fetchJson(
    `${API_BASE}/progress/${encodeURIComponent(studentId)}`
  )

  if (!Array.isArray(data)) {
    throw new ProgressApiError(
      'The backend returned an unexpected progress response.',
      'invalid-response'
    )
  }

  return data
}

export async function loadTopicProgress(studentId) {
  const data = await fetchJson(
    `${API_BASE}/progress/${encodeURIComponent(studentId)}/topics`
  )

  if (!Array.isArray(data)) {
    throw new ProgressApiError(
      'The backend returned an unexpected progress response.',
      'invalid-response'
    )
  }

  return data
}