import { useState } from 'react'
import {
  InterviewApiError,
  loadInterviewSessionSummary,
  loadNextInterviewQuestion,
  startInterviewSession,
  submitInterviewAnswer,
} from '../services/interviewApi.js'
import '../styles/interview.css'

const modes = [
  { value: 'TECHNICAL', label: 'Technical' },
  { value: 'HR', label: 'HR' },
  { value: 'PROJECT', label: 'Project' },
]

const topicsByMode = {
  TECHNICAL: [
    { value: 'DSA', label: 'DSA' },
    { value: 'DBMS', label: 'DBMS' },
    { value: 'Operating Systems', label: 'Operating Systems' },
    { value: 'Computer Networks', label: 'Computer Networks' },
    { value: 'OOP', label: 'OOP' },
    { value: 'Java', label: 'Java' },
    { value: 'Python', label: 'Python' },
    { value: 'AI/ML', label: 'AI/ML' },
  ],
  HR: [
    { value: 'Tell Me About Yourself', label: 'Tell Me About Yourself' },
    { value: 'Strengths and Weaknesses', label: 'Strengths / Weaknesses' },
    { value: 'Motivation', label: 'Motivation' },
    { value: 'Behavioral', label: 'Behavioral' },
    { value: 'Teamwork', label: 'Teamwork' },
    { value: 'Leadership', label: 'Leadership' },
    { value: 'Career Goals', label: 'Career Goals' },
    { value: 'Conflict Resolution', label: 'Conflict Resolution' },
  ],
  PROJECT: [
    { value: 'Project Introduction', label: 'Project Introduction' },
    { value: 'Architecture', label: 'Architecture' },
    { value: 'Technology Choices', label: 'Technology Choices' },
    { value: 'Implementation', label: 'Implementation' },
    { value: 'Challenges', label: 'Challenges' },
    { value: 'Testing', label: 'Testing' },
    { value: 'Deployment', label: 'Deployment' },
    { value: 'Future Improvements', label: 'Future Improvements' },
  ],
}

const difficulties = ['Easy', 'Medium', 'Hard']
const questionCounts = [1, 3, 5, 10, 20]

function InterviewPage({ onNavigate, selectedStudentId }) {
  const [mode, setMode] = useState('TECHNICAL')
  const [topic, setTopic] = useState('DBMS')
  const [difficulty, setDifficulty] = useState('Medium')
  const [totalQuestions, setTotalQuestions] = useState(3)
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const [session, setSession] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [summary, setSummary] = useState(null)
  const [answer, setAnswer] = useState('')
  const [busyAction, setBusyAction] = useState('')
  const [error, setError] = useState('')
  const [summaryError, setSummaryError] = useState('')

  const studentNumber = Number(selectedStudentId)
  const hasStudent = Number.isInteger(studentNumber) && studentNumber > 0
  const question = session?.question
  const completed = evaluation?.status === 'completed' || summary?.status === 'completed'
  const topics = topicsByMode[mode]

  function resetInterview() {
    setSession(null)
    setEvaluation(null)
    setSummary(null)
    setAnswer('')
    setError('')
    setSummaryError('')
  }

  function handleModeChange(value) {
    setMode(value)
    setTopic(topicsByMode[value][0].value)
  }

  async function handleStart(event) {
    event.preventDefault()
    resetInterview()
    setBusyAction('start')
    try {
      setSession(await startInterviewSession({
        mode,
        topic,
        difficulty,
        totalQuestions,
        studentId: studentNumber,
        projectName,
        projectDescription,
      }))
    } catch (startError) {
      setError(startError instanceof InterviewApiError ? startError.message : 'Could not start the interview.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleAnswer(event) {
    event.preventDefault()
    if (!session || !question || !answer.trim()) {
      setError('Enter your answer before submitting.')
      return
    }
    setBusyAction('answer')
    setError('')
    try {
      const result = await submitInterviewAnswer(session.session_id, question.question_id, answer.trim())
      setEvaluation(result)
      if (result.status === 'completed') {
        try {
          setSummary(await loadInterviewSessionSummary(session.session_id))
        } catch (summaryLoadError) {
          setSummaryError(summaryLoadError instanceof InterviewApiError ? summaryLoadError.message : 'Could not load the completed interview summary.')
        }
      }
    } catch (answerError) {
      setError(answerError instanceof InterviewApiError ? answerError.message : 'Could not submit this answer.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleNext() {
    if (!session || completed) return
    setBusyAction('next')
    setError('')
    try {
      setSession(await loadNextInterviewQuestion(session.session_id))
      setEvaluation(null)
      setAnswer('')
    } catch (nextError) {
      setError(nextError instanceof InterviewApiError ? nextError.message : 'Could not load the next interview question.')
    } finally {
      setBusyAction('')
    }
  }

  function renderError(message) {
    return (
      <div className="alert alert-error interview-alert" role="alert">
        <span aria-hidden="true">!</span>
        <p>{message}</p>
      </div>
    )
  }

  return (
    <div className="dashboard-page interview-page">
      <section className="page-heading interview-page-heading">
        <div>
          <p className="eyebrow">PRACTICE THE CONVERSATION</p>
          <h1>Interview Practice</h1>
          <p className="page-subtitle">Build clear, confident answers with realistic placement practice.</p>
        </div>
        <span className="interview-heading-mark" aria-hidden="true">“ ”</span>
      </section>

      {!hasStudent && (
        <div className="student-required-note" role="status">
          <span className="student-required-icon" aria-hidden="true">i</span>
          <div>
            <strong>Choose a student first</strong>
            <p>Load a student ID on the Dashboard to link this interview to their progress.</p>
          </div>
          <button className="button button-secondary" onClick={() => onNavigate('dashboard')} type="button">Go to Dashboard</button>
        </div>
      )}

      {!session ? (
        <section className="interview-setup-card">
          <div className="interview-setup-intro">
            <div className="interview-section-icon" aria-hidden="true">01</div>
            <div>
              <p className="eyebrow">SESSION SETUP</p>
              <h2>Choose your interview focus</h2>
              <p>Questions are conversational and open-ended, just like an interview.</p>
            </div>
          </div>
          <form onSubmit={handleStart}>
            <div className="interview-select-grid">
              <label className="interview-field" htmlFor="interview-mode">
                <span>Mode</span>
                <select id="interview-mode" onChange={(event) => handleModeChange(event.target.value)} value={mode}>
                  {modes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>
              <label className="interview-field" htmlFor="interview-topic">
                <span>Topic</span>
                <select id="interview-topic" onChange={(event) => setTopic(event.target.value)} value={topic}>
                  {topics.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>
              <label className="interview-field" htmlFor="interview-difficulty">
                <span>Difficulty</span>
                <select id="interview-difficulty" onChange={(event) => setDifficulty(event.target.value)} value={difficulty}>
                  {difficulties.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label className="interview-field" htmlFor="interview-count">
                <span>Questions</span>
                <select id="interview-count" onChange={(event) => setTotalQuestions(Number(event.target.value))} value={totalQuestions}>
                  {questionCounts.map((item) => <option key={item} value={item}>{item} {item === 1 ? 'question' : 'questions'}</option>)}
                </select>
              </label>
            </div>

            {mode === 'PROJECT' && (
              <div className="project-context-fields">
                <label className="interview-field" htmlFor="project-name">
                  <span>Project name <small>Optional</small></span>
                  <input id="project-name" maxLength="200" onChange={(event) => setProjectName(event.target.value)} placeholder="e.g. Placify" value={projectName} />
                </label>
                <label className="interview-field" htmlFor="project-description">
                  <span>Project description <small>Optional</small></span>
                  <textarea id="project-description" maxLength="8000" onChange={(event) => setProjectDescription(event.target.value)} placeholder="Describe what it does, how it is built, and the problem it solves..." rows="3" value={projectDescription} />
                </label>
              </div>
            )}

            {error && renderError(error)}
            <div className="interview-start-row">
              <p>The interviewer will ask one question at a time.</p>
              <button className="button button-primary interview-start-button" disabled={Boolean(busyAction) || !hasStudent} type="submit">
                {busyAction === 'start' ? <span className="button-spinner" aria-hidden="true" /> : null}
                {busyAction === 'start' ? 'Starting interview' : 'Start Interview'}
                {busyAction !== 'start' && <span aria-hidden="true">→</span>}
              </button>
            </div>
          </form>
        </section>
      ) : (
        <>
          <div className="interview-session-strip">
            <div className="interview-session-meta">
              <span className="interview-mode-chip">{modes.find((item) => item.value === question.mode)?.label ?? question.mode}</span>
              <span className="interview-topic-chip">{question.topic}</span>
              <span className="interview-question-type">{question.question_type === 'FOLLOW_UP' ? 'Follow-up' : 'Open-ended'}</span>
              <span className="interview-question-count">Question {session.question_number} of {session.total_questions}</span>
            </div>
            {!completed && <button className="text-button" disabled={Boolean(busyAction)} onClick={resetInterview} type="button">End interview</button>}
          </div>

          {error && renderError(error)}

          <section className="interview-question-card">
            <div className="interview-question-heading">
              <div>
                <p className="eyebrow">QUESTION {String(session.question_number).padStart(2, '0')}</p>
                <h2>Take a moment to organize your thoughts.</h2>
              </div>
              <span className="interview-question-mark" aria-hidden="true">“</span>
            </div>
            <p className="interview-question-text">{question.question}</p>
            {!evaluation && <p className="interview-answer-note">Answer in your own words. Specific examples help make a response clear.</p>}
          </section>

          {!completed && (
            <section className="interview-answer-card">
              <div className="interview-answer-title">
                <div className="interview-section-icon answer-icon" aria-hidden="true">02</div>
                <div>
                  <p className="eyebrow">YOUR RESPONSE</p>
                  <h2>How would you answer?</h2>
                </div>
              </div>
              {!evaluation ? (
                <form onSubmit={handleAnswer}>
                  <label className="interview-answer-label" htmlFor="interview-answer">Your answer</label>
                  <textarea id="interview-answer" maxLength="12000" onChange={(event) => setAnswer(event.target.value)} placeholder="Share your answer as you would in an interview..." rows="7" value={answer} />
                  {error && renderError(error)}
                  <div className="interview-submit-row">
                    <span>Your answer is evaluated on its content and structure.</span>
                    <button className="button button-primary" disabled={Boolean(busyAction) || !answer.trim()} type="submit">
                      {busyAction === 'answer' ? <span className="button-spinner" aria-hidden="true" /> : null}
                      {busyAction === 'answer' ? 'Reviewing answer' : 'Submit Answer'}
                      {busyAction !== 'answer' && <span aria-hidden="true">→</span>}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="interview-evaluation">
                  <div className="interview-score-line">
                    <div><span>Practice score</span><strong>{Number(evaluation.score).toFixed(1)}<small> / 10</small></strong></div>
                    <p>{evaluation.feedback}</p>
                  </div>
                  <div className="interview-feedback-grid">
                    <div><h3>Strengths</h3>{evaluation.strengths.length ? <ul>{evaluation.strengths.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul> : <p>No strengths returned.</p>}</div>
                    <div><h3>Areas to improve</h3>{evaluation.weaknesses.length || evaluation.missing_points.length ? <ul>{[...evaluation.weaknesses, ...evaluation.missing_points].map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul> : <p>No missing points returned.</p>}</div>
                    <div><h3>Communication</h3><p>{evaluation.communication_feedback}</p></div>
                    <div><h3>Technical feedback</h3><p>{evaluation.technical_feedback}</p></div>
                  </div>
                  <div className="suggested-answer"><h3>Example of a stronger answer</h3><p>{evaluation.suggested_answer}</p></div>
                </div>
              )}
            </section>
          )}

          {completed ? (
            <section className="interview-summary-card">
              <div className="interview-summary-check" aria-hidden="true">✓</div>
              <div className="interview-summary-main">
                <p className="eyebrow">INTERVIEW COMPLETE</p>
                <h2>Session summary</h2>
                {summaryError && <p className="interview-summary-warning">{summaryError}</p>}
                {summary && (
                  <>
                    <div className="interview-summary-metrics">
                      <div><span>Questions answered</span><strong>{summary.questions_answered} / {summary.total_questions}</strong></div>
                      <div><span>Average score</span><strong>{Number(summary.average_score).toFixed(1)} / 10</strong></div>
                      <div><span>Status</span><strong className="interview-status">{summary.status}</strong></div>
                    </div>
                    {summary.strengths.length > 0 && <p className="summary-list-line"><strong>Strengths</strong>{summary.strengths.join(' · ')}</p>}
                    {summary.areas_to_improve.length > 0 && <p className="summary-list-line"><strong>Areas to improve</strong>{summary.areas_to_improve.join(' · ')}</p>}
                    <p className="interview-overall-feedback">{summary.overall_feedback}</p>
                  </>
                )}
                <button className="button button-primary" onClick={resetInterview} type="button">Start another interview</button>
              </div>
            </section>
          ) : evaluation ? (
            <div className="interview-next-row">
              <p>The next question may follow up on your answer.</p>
              <button className="button button-primary" disabled={Boolean(busyAction)} onClick={handleNext} type="button">
                {busyAction === 'next' ? <span className="button-spinner" aria-hidden="true" /> : null}
                {busyAction === 'next' ? 'Preparing follow-up' : 'Next Question'}
                {busyAction !== 'next' && <span aria-hidden="true">→</span>}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}

export default InterviewPage