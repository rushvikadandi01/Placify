const API_BASE = '/api'

export class ProgressApiError extends Error {
  constructor(message, code) {
    super(message)
    this.name = 'ProgressApiError'
    this.code = code
  }
}

export async function loadProgressSummary(studentId) {
  let response
  try {
    response = await fetch(`${API_BASE}/progress/${encodeURIComponent(studentId)}/summary`)
  } catch {
    throw new ProgressApiError('Could not connect to the backend.', 'unavailable')
  }

  if (response.status === 404) {
    throw new ProgressApiError('Student not found.', 'not-found')
  }
  if (!response.ok) {
    throw new ProgressApiError('Something went wrong while loading progress.', 'request-failed')
  }

  let data
  try {
    data = await response.json()
  } catch {
    throw new ProgressApiError('The backend returned an unexpected progress response.', 'invalid-response')
  }

  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new ProgressApiError('The backend returned an unexpected progress response.', 'invalid-response')
  }

  return data
}