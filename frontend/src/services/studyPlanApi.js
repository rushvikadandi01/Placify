const API_BASE = '/api'

export class StudyPlanApiError extends Error {
  constructor(message, code) {
    super(message)
    this.name = 'StudyPlanApiError'
    this.code = code
  }
}

export async function generateStudyPlan(payload) {
  let response

  try {
    response = await fetch(`${API_BASE}/study-plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new StudyPlanApiError(
      'Could not connect to the backend.',
      'unavailable'
    )
  }

  if (response.status === 404) {
    throw new StudyPlanApiError(
      'Student not found. Load progress for a valid student first.',
      'not-found'
    )
  }

  if (response.status === 422) {
    throw new StudyPlanApiError(
      'Please check the study plan details and try again.',
      'validation'
    )
  }

  if (response.status === 502) {
    throw new StudyPlanApiError(
      'The AI provider could not generate the study plan. Please try again later.',
      'provider'
    )
  }

  if (response.status === 503) {
    throw new StudyPlanApiError(
      'AI service is not configured correctly.',
      'configuration'
    )
  }

  if (response.status === 504) {
    throw new StudyPlanApiError(
      'The AI provider took too long to respond. Please try again.',
      'timeout'
    )
  }

  if (!response.ok) {
    throw new StudyPlanApiError(
      'Something went wrong while generating the study plan.',
      'request-failed'
    )
  }

  try {
    return await response.json()
  } catch {
    throw new StudyPlanApiError(
      'The backend returned an unexpected study plan response.',
      'invalid-response'
    )
  }
}