const API_BASE = '/api'

export class DsaApiError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'DsaApiError'
    this.status = status
  }
}

async function requestJson(path, { method = 'GET', body } = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new DsaApiError('Could not connect to the backend.')
  }

  if (!response.ok) {
    const messages = {
      404: 'This practice session or question could not be found. Start a new session.',
      409: 'That action is not available right now. Check the current question or start a new session.',
      422: 'Check the selected topic, difficulty, question count, and answer, then try again.',
      502: 'The AI practice service could not complete that request. Please try again.',
      503: 'The AI practice service is not configured right now.',
      504: 'The AI practice service timed out. Please try again.',
    }
    throw new DsaApiError(messages[response.status] ?? 'Something went wrong. Please try again.', response.status)
  }

  try {
    return await response.json()
  } catch {
    throw new DsaApiError('The backend returned an unexpected response.', response.status)
  }
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function validateQuestionEnvelope(data) {
  const question = data?.question
  if (
    !isObject(data)
    || typeof data.session_id !== 'string'
    || !Number.isInteger(data.question_number)
    || !Number.isInteger(data.total_questions)
    || !isObject(question)
    || typeof question.question_id !== 'string'
    || typeof question.topic !== 'string'
    || typeof question.difficulty !== 'string'
    || typeof question.title !== 'string'
    || typeof question.problem !== 'string'
    || !Array.isArray(question.examples)
    || !Array.isArray(question.constraints)
  ) {
    throw new DsaApiError('The backend returned an unexpected question format.')
  }
  return data
}

export async function startDsaSession({ topic, difficulty, totalQuestions, studentId }) {
  const body = {
    topic,
    difficulty,
    total_questions: totalQuestions,
  }
  if (studentId !== null && studentId !== undefined) {
    body.student_id = studentId
  }
  return validateQuestionEnvelope(await requestJson('/dsa/session/start', { method: 'POST', body }))
}

export async function submitDsaAttempt(sessionId, { questionId, attempt }) {
  const data = await requestJson(`/dsa/session/${encodeURIComponent(sessionId)}/attempt`, {
    method: 'POST',
    body: { question_id: questionId, attempt },
  })
  if (
    !isObject(data)
    || typeof data.is_correct !== 'boolean'
    || typeof data.feedback !== 'string'
    || !Array.isArray(data.mistakes)
    || !Array.isArray(data.edge_cases)
    || typeof data.time_complexity !== 'string'
    || typeof data.space_complexity !== 'string'
    || typeof data.status !== 'string'
  ) {
    throw new DsaApiError('The backend returned an unexpected evaluation format.')
  }
  return data
}

export async function requestDsaHint({ questionId, sessionId, attempt, hintLevel }) {
  const data = await requestJson('/dsa/hint', {
    method: 'POST',
    body: {
      question_id: questionId,
      attempt,
      hint_level: hintLevel,
      session_id: sessionId,
    },
  })
  if (!isObject(data) || typeof data.hint !== 'string' || !Number.isInteger(data.hint_level)) {
    throw new DsaApiError('The backend returned an unexpected hint format.')
  }
  return data
}

export async function loadNextDsaQuestion(sessionId) {
  return validateQuestionEnvelope(await requestJson(
    `/dsa/session/${encodeURIComponent(sessionId)}/next`,
    { method: 'POST' },
  ))
}

export async function loadDsaSessionSummary(sessionId) {
  const data = await requestJson(`/dsa/session/${encodeURIComponent(sessionId)}`)
  if (
    !isObject(data)
    || typeof data.status !== 'string'
    || typeof data.topic !== 'string'
    || typeof data.difficulty !== 'string'
    || !Number.isInteger(data.total_questions)
    || !Number.isInteger(data.questions_attempted)
    || !Number.isInteger(data.questions_correct)
    || !Number.isFinite(data.accuracy)
    || !Number.isInteger(data.hints_used)
  ) {
    throw new DsaApiError('The backend returned an unexpected session summary format.')
  }
  return data
}