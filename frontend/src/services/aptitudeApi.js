const API_BASE = '/api'

export class AptitudeApiError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'AptitudeApiError'
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
    throw new AptitudeApiError('Could not connect to the backend.')
  }

  if (!response.ok) {
    const messages = {
      404: 'This practice session or question could not be found. Start a new practice session.',
      409: 'That action is not available right now. Check the current question or start a new session.',
      422: 'Check the category, topic, difficulty, and selected answer, then try again.',
      502: 'The AI practice service could not complete that request. Please try again.',
      503: 'The AI practice service is not configured right now.',
      504: 'The AI practice service timed out. Please try again.',
    }
    throw new AptitudeApiError(messages[response.status] ?? 'Something went wrong. Please try again.', response.status)
  }

  try {
    return await response.json()
  } catch {
    throw new AptitudeApiError('The backend returned an unexpected response.', response.status)
  }
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function validateQuestion(data) {
  const hasExposedAnswer = isObject(data) && ('correct_answer' in data || 'explanation' in data)
  if (
    !isObject(data)
    || typeof data.question_id !== 'string'
    || typeof data.question !== 'string'
    || !Array.isArray(data.options)
    || data.options.length !== 4
    || !data.options.every((option) => typeof option === 'string')
    || new Set(data.options.map((option) => option.toLowerCase())).size !== 4
    || typeof data.category !== 'string'
    || typeof data.topic !== 'string'
    || typeof data.difficulty !== 'string'
    || hasExposedAnswer
  ) {
    throw new AptitudeApiError('The backend returned an unexpected question format.')
  }
  return data
}

function validateSessionQuestion(data) {
  if (
    !isObject(data)
    || typeof data.session_id !== 'string'
    || !Number.isInteger(data.question_number)
    || !Number.isInteger(data.total_questions)
  ) {
    throw new AptitudeApiError('The backend returned an unexpected session format.')
  }
  return { ...data, question: validateQuestion(data.question) }
}

function validateEvaluation(data) {
  if (
    !isObject(data)
    || typeof data.is_correct !== 'boolean'
    || typeof data.selected_answer !== 'string'
    || typeof data.correct_answer !== 'string'
    || typeof data.explanation !== 'string'
    || typeof data.learning_feedback !== 'string'
  ) {
    throw new AptitudeApiError('The backend returned an unexpected answer result.')
  }
  return data
}

export async function requestAptitudeQuestion({ category, topic, difficulty }) {
  return validateQuestion(await requestJson('/aptitude/question', {
    method: 'POST',
    body: { category, topic, difficulty },
  }))
}

export async function submitAptitudeAnswer(questionId, selectedAnswer) {
  return validateEvaluation(await requestJson('/aptitude/attempt', {
    method: 'POST',
    body: { question_id: questionId, selected_answer: selectedAnswer },
  }))
}

export async function startAptitudeSession({ category, topic, difficulty, totalQuestions, studentId }) {
  const body = {
    category,
    topic,
    difficulty,
    total_questions: totalQuestions,
  }
  if (studentId !== null && studentId !== undefined) body.student_id = studentId
  return validateSessionQuestion(await requestJson('/aptitude/session/start', { method: 'POST', body }))
}

export async function submitAptitudeSessionAnswer(sessionId, questionId, selectedAnswer) {
  const data = validateEvaluation(await requestJson(
    `/aptitude/session/${encodeURIComponent(sessionId)}/attempt`,
    { method: 'POST', body: { question_id: questionId, selected_answer: selectedAnswer } },
  ))
  if (typeof data.status !== 'string' || !Number.isInteger(data.questions_attempted) || !Number.isInteger(data.questions_correct)) {
    throw new AptitudeApiError('The backend returned an unexpected session result.')
  }
  return data
}

export async function loadNextAptitudeQuestion(sessionId) {
  return validateSessionQuestion(await requestJson(
    `/aptitude/session/${encodeURIComponent(sessionId)}/next`,
    { method: 'POST' },
  ))
}

export async function loadAptitudeSessionSummary(sessionId) {
  const data = await requestJson(`/aptitude/session/${encodeURIComponent(sessionId)}`)
  if (
    !isObject(data)
    || typeof data.status !== 'string'
    || typeof data.category !== 'string'
    || typeof data.topic !== 'string'
    || typeof data.difficulty !== 'string'
    || !Number.isInteger(data.total_questions)
    || !Number.isInteger(data.questions_attempted)
    || !Number.isInteger(data.questions_correct)
    || !Number.isFinite(data.accuracy)
  ) {
    throw new AptitudeApiError('The backend returned an unexpected session summary format.')
  }
  return data
}