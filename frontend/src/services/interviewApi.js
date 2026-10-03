const API_BASE = '/api'

export class InterviewApiError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'InterviewApiError'
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
    throw new InterviewApiError('Could not connect to the backend.')
  }

  if (!response.ok) {
    const messages = {
      404: 'This interview session could not be found. Start a new session.',
      409: 'That action is not available right now. Check the current question or start a new session.',
      422: 'Check the selected mode, topic, and answer, then try again.',
      502: 'The AI interview service could not complete that request. Please try again.',
      503: 'The AI interview service is not configured right now.',
      504: 'The AI interview service timed out. Please try again.',
    }
    throw new InterviewApiError(messages[response.status] ?? 'Something went wrong. Please try again.', response.status)
  }

  try {
    return await response.json()
  } catch {
    throw new InterviewApiError('The backend returned an unexpected response.', response.status)
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
    || typeof question.question !== 'string'
    || typeof question.mode !== 'string'
    || typeof question.topic !== 'string'
    || typeof question.question_type !== 'string'
  ) {
    throw new InterviewApiError('The backend returned an unexpected interview question format.')
  }
  return data
}

function validateEvaluation(data) {
  if (
    !isObject(data)
    || typeof data.question_id !== 'string'
    || !Number.isFinite(data.score)
    || !Array.isArray(data.strengths)
    || !Array.isArray(data.weaknesses)
    || typeof data.feedback !== 'string'
    || !Array.isArray(data.missing_points)
    || typeof data.suggested_answer !== 'string'
    || typeof data.communication_feedback !== 'string'
    || typeof data.technical_feedback !== 'string'
  ) {
    throw new InterviewApiError('The backend returned an unexpected interview evaluation format.')
  }
  return data
}

export async function startInterviewSession({ mode, topic, difficulty, totalQuestions, studentId, projectName, projectDescription }) {
  const body = {
    mode,
    topic,
    difficulty,
    total_questions: totalQuestions,
  }
  if (studentId !== null && studentId !== undefined) body.student_id = studentId
  if (projectName?.trim()) body.project_name = projectName.trim()
  if (projectDescription?.trim()) body.project_description = projectDescription.trim()
  return validateQuestionEnvelope(await requestJson('/interview/session/start', { method: 'POST', body }))
}

export async function submitInterviewAnswer(sessionId, questionId, answer) {
  const data = validateEvaluation(await requestJson(
    `/interview/session/${encodeURIComponent(sessionId)}/answer`,
    { method: 'POST', body: { question_id: questionId, answer } },
  ))
  if (
    typeof data.session_id !== 'string'
    || !Number.isInteger(data.questions_attempted)
    || !Number.isFinite(data.average_score)
    || typeof data.status !== 'string'
  ) {
    throw new InterviewApiError('The backend returned an unexpected interview session result.')
  }
  return data
}

export async function loadNextInterviewQuestion(sessionId) {
  return validateQuestionEnvelope(await requestJson(
    `/interview/session/${encodeURIComponent(sessionId)}/next`,
    { method: 'POST' },
  ))
}

export async function loadInterviewSessionSummary(sessionId) {
  const data = await requestJson(`/interview/session/${encodeURIComponent(sessionId)}`)
  if (
    !isObject(data)
    || typeof data.session_id !== 'string'
    || typeof data.mode !== 'string'
    || typeof data.topic !== 'string'
    || !Number.isInteger(data.total_questions)
    || !Number.isInteger(data.questions_answered)
    || !Number.isFinite(data.average_score)
    || typeof data.status !== 'string'
    || !Array.isArray(data.strengths)
    || !Array.isArray(data.areas_to_improve)
    || typeof data.overall_feedback !== 'string'
  ) {
    throw new InterviewApiError('The backend returned an unexpected interview summary format.')
  }
  return data
}