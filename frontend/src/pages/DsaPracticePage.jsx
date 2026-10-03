import { useState } from 'react'
import {
  DsaApiError,
  loadDsaSessionSummary,
  loadNextDsaQuestion,
  requestDsaHint,
  startDsaSession,
  submitDsaAttempt,
} from '../services/dsaApi.js'
import '../styles/dsa.css'

const topics = [
  'Arrays',
  'Strings',
  'HashMap',
  'HashSet',
  'Linked List',
  'Stack',
  'Queue',
  'Binary Tree',
  'BST',
  'Heap',
  'Graph',
  'Recursion',
  'Sorting',
  'Searching',
  'Dynamic Programming',
]

const difficulties = ['Easy', 'Medium', 'Hard']
const questionCounts = [1, 3, 5, 10, 20]

function DsaPracticePage({ onNavigate, selectedStudentId }) {
  const [topic, setTopic] = useState('Arrays')
  const [difficulty, setDifficulty] = useState('Easy')
  const [totalQuestions, setTotalQuestions] = useState(3)
  const [session, setSession] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [summary, setSummary] = useState(null)
  const [answer, setAnswer] = useState('')
  const [hint, setHint] = useState('')
  const [hintLevel, setHintLevel] = useState(0)
  const [busyAction, setBusyAction] = useState('')
  const [error, setError] = useState('')
  const [summaryError, setSummaryError] = useState('')

  const studentNumber = Number(selectedStudentId)
  const hasStudent = Number.isInteger(studentNumber) && studentNumber > 0
  const question = session?.question
  const completed = evaluation?.status === 'completed' || summary?.status === 'completed'

  async function handleStart(event) {
    event.preventDefault()
    setBusyAction('start')
    setError('')
    setSummaryError('')
    setSession(null)
    setEvaluation(null)
    setSummary(null)
    setHint('')
    setHintLevel(0)
    setAnswer('')
    try {
      const started = await startDsaSession({
        topic,
        difficulty,
        totalQuestions,
        studentId: studentNumber,
      })
      setSession(started)
    } catch (startError) {
      setError(startError instanceof DsaApiError ? startError.message : 'Could not start DSA practice.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!session || !question || !answer.trim()) {
      setError('Write your approach or code before submitting.')
      return
    }
    setBusyAction('submit')
    setError('')
    try {
      const result = await submitDsaAttempt(session.session_id, {
        questionId: question.question_id,
        attempt: answer.trim(),
      })
      setEvaluation(result)
      if (result.status === 'completed') {
        try {
          setSummary(await loadDsaSessionSummary(session.session_id))
        } catch (summaryLoadError) {
          setSummaryError(
            summaryLoadError instanceof DsaApiError
              ? summaryLoadError.message
              : 'Could not load the completed session summary.',
          )
        }
      }
    } catch (submitError) {
      setError(submitError instanceof DsaApiError ? submitError.message : 'Could not submit this answer.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleHint() {
    if (!session || !question || hintLevel >= 3) return
    setBusyAction('hint')
    setError('')
    try {
      const result = await requestDsaHint({
        questionId: question.question_id,
        sessionId: session.session_id,
        attempt: answer.trim(),
        hintLevel: hintLevel + 1,
      })
      setHint(result.hint)
      setHintLevel(result.hint_level)
    } catch (hintError) {
      setError(hintError instanceof DsaApiError ? hintError.message : 'Could not load a hint.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleNext() {
    if (!session || completed) return
    setBusyAction('next')
    setError('')
    try {
      setSession(await loadNextDsaQuestion(session.session_id))
      setEvaluation(null)
      setHint('')
      setHintLevel(0)
      setAnswer('')
    } catch (nextError) {
      setError(nextError instanceof DsaApiError ? nextError.message : 'Could not load the next question.')
    } finally {
      setBusyAction('')
    }
  }

  function renderError(loadError) {
    return (
      <div className="alert alert-error dsa-alert" role="alert">
        <span aria-hidden="true">!</span>
        <p>{loadError}</p>
      </div>
    )
  }

  return (
    <div className="dashboard-page dsa-page">
      <section className="page-heading dsa-page-heading">
        <div>
          <p className="eyebrow">PRACTICE WITH INTENTION</p>
          <h1>DSA Practice</h1>
          <p className="page-subtitle">Practice coding concepts with your AI placement mentor.</p>
        </div>
        <span className="dsa-heading-mark" aria-hidden="true">{`{ }`}</span>
      </section>

      {!hasStudent && (
        <div className="student-required-note" role="status">
          <span className="student-required-icon" aria-hidden="true">i</span>
          <div>
            <strong>Choose a student first</strong>
            <p>Load a student ID on the Dashboard so this practice session can be linked to their progress.</p>
          </div>
          <button className="button button-secondary" onClick={() => onNavigate('dashboard')} type="button">
            Go to Dashboard
          </button>
        </div>
      )}

      {!session ? (
        <section className="dsa-setup-card">
          <div className="dsa-setup-intro">
            <div className="dsa-section-icon" aria-hidden="true">01</div>
            <div>
              <p className="eyebrow">SESSION SETUP</p>
              <h2>Choose what to practice</h2>
              <p>Pick a topic and difficulty. Your mentor will bring one problem at a time.</p>
            </div>
          </div>
          <form onSubmit={handleStart}>
            <div className="dsa-select-grid">
              <label className="dsa-field" htmlFor="dsa-topic">
                <span>Topic</span>
                <select id="dsa-topic" onChange={(event) => setTopic(event.target.value)} value={topic}>
                  {topics.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label className="dsa-field" htmlFor="dsa-difficulty">
                <span>Difficulty</span>
                <select id="dsa-difficulty" onChange={(event) => setDifficulty(event.target.value)} value={difficulty}>
                  {difficulties.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label className="dsa-field" htmlFor="dsa-count">
                <span>Questions</span>
                <select id="dsa-count" onChange={(event) => setTotalQuestions(Number(event.target.value))} value={totalQuestions}>
                  {questionCounts.map((item) => <option key={item} value={item}>{item} {item === 1 ? 'question' : 'questions'}</option>)}
                </select>
              </label>
            </div>
            {error && renderError(error)}
            <div className="dsa-start-row">
              <p>Questions are generated for your selected topic and difficulty.</p>
              <button className="button button-primary dsa-start-button" disabled={Boolean(busyAction) || !hasStudent} type="submit">
                {busyAction === 'start' ? <span className="button-spinner" aria-hidden="true" /> : null}
                {busyAction === 'start' ? 'Starting session' : 'Start Practice'}
                {busyAction !== 'start' && <span aria-hidden="true">→</span>}
              </button>
            </div>
          </form>
        </section>
      ) : (
        <>
          <div className="dsa-session-strip">
            <div className="dsa-session-meta">
              <span className="dsa-topic-chip">{question.topic}</span>
              <span className={`dsa-difficulty-chip difficulty-${question.difficulty.toLowerCase()}`}>{question.difficulty}</span>
              <span className="dsa-question-count">Question {session.question_number} of {session.total_questions}</span>
            </div>
            {!completed && (
              <button
                className="text-button"
                disabled={Boolean(busyAction)}
                onClick={() => {
                  setSession(null)
                  setEvaluation(null)
                  setSummary(null)
                  setHint('')
                  setHintLevel(0)
                  setAnswer('')
                  setError('')
                }}
                type="button"
              >
                End session
              </button>
            )}
          </div>

          {error && renderError(error)}

          <div className="dsa-workspace">
            <section className="dsa-question-card">
              <div className="dsa-question-heading">
                <div>
                  <p className="eyebrow">PROBLEM {String(session.question_number).padStart(2, '0')}</p>
                  <h2>{question.title}</h2>
                </div>
                <span className="question-type-mark" aria-hidden="true">Q</span>
              </div>
              <div className="dsa-problem-text">{question.problem}</div>

              {question.examples.length > 0 && (
                <div className="dsa-question-section">
                  <h3>Examples</h3>
                  <div className="dsa-example-list">
                    {question.examples.map((example, index) => (
                      <div className="dsa-example" key={`${question.question_id}-example-${index}`}>
                        <span className="example-number">{String(index + 1).padStart(2, '0')}</span>
                        <div>
                          <p><strong>Input</strong><code>{example.input}</code></p>
                          <p><strong>Output</strong><code>{example.output}</code></p>
                          {example.explanation && <p className="example-explanation">{example.explanation}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {question.constraints.length > 0 && (
                <div className="dsa-question-section constraints-section">
                  <h3>Constraints</h3>
                  <ul>{question.constraints.map((constraint, index) => <li key={`${index}-${constraint}`}>{constraint}</li>)}</ul>
                </div>
              )}

              {!evaluation && !completed && (
                <div className="dsa-hint-row">
                  <div>
                    <strong>{hintLevel ? `Hint ${hintLevel} of 3` : 'Want a nudge?'}</strong>
                    {hint && <p className="dsa-hint-text">{hint}</p>}
                    {!hint && <p>Hints reveal gradually, only when you ask.</p>}
                  </div>
                  <button
                    className="button button-secondary hint-button"
                    disabled={Boolean(busyAction) || hintLevel >= 3}
                    onClick={handleHint}
                    type="button"
                  >
                    {busyAction === 'hint' ? 'Getting hint' : hintLevel === 0 ? 'Get Hint' : hintLevel >= 3 ? 'All hints used' : 'Next Hint'}
                  </button>
                </div>
              )}
            </section>

            {!completed && (
              <section className="dsa-answer-card">
                <div className="dsa-answer-heading">
                  <div className="dsa-section-icon answer-section-icon" aria-hidden="true">02</div>
                  <div>
                    <p className="eyebrow">YOUR APPROACH</p>
                    <h2>How would you solve it?</h2>
                  </div>
                </div>
                {!evaluation ? (
                  <form onSubmit={handleSubmit}>
                    <label className="answer-label" htmlFor="dsa-answer">Your answer or approach</label>
                    <textarea
                      id="dsa-answer"
                      onChange={(event) => setAnswer(event.target.value)}
                      placeholder="Describe your approach or paste your code..."
                      rows="8"
                      value={answer}
                    />
                    <div className="answer-footer">
                      <span>Share your thinking, even if you’re unsure.</span>
                      <button className="button button-primary" disabled={Boolean(busyAction)} type="submit">
                        {busyAction === 'submit' ? <span className="button-spinner" aria-hidden="true" /> : null}
                        {busyAction === 'submit' ? 'Reviewing' : 'Submit Answer'}
                        {busyAction !== 'submit' && <span aria-hidden="true">→</span>}
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className={`dsa-evaluation${evaluation.is_correct ? ' evaluation-correct' : ' evaluation-review'}`}>
                    <div className="evaluation-result">
                      <span aria-hidden="true">{evaluation.is_correct ? '✓' : '↗'}</span>
                      <strong>{evaluation.is_correct ? 'Good work' : 'Review and learn'}</strong>
                    </div>
                    <p className="evaluation-feedback">{evaluation.feedback}</p>
                    {evaluation.mistakes.length > 0 && (
                      <div className="evaluation-list">
                        <strong>Points to revisit</strong>
                        <ul>{evaluation.mistakes.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
                      </div>
                    )}
                    {evaluation.edge_cases.length > 0 && (
                      <div className="evaluation-list">
                        <strong>Consider these edge cases</strong>
                        <ul>{evaluation.edge_cases.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
                      </div>
                    )}
                    <div className="complexity-row">
                      <span><strong>Time</strong>{evaluation.time_complexity}</span>
                      <span><strong>Space</strong>{evaluation.space_complexity}</span>
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>

          {completed ? (
            <section className="dsa-summary-card">
              <div className="summary-check" aria-hidden="true">✓</div>
              <div className="summary-main">
                <p className="eyebrow">SESSION COMPLETE</p>
                <h2>Practice logged. Nice work.</h2>
                {summaryError && <p className="summary-warning">{summaryError}</p>}
                {summary && (
                  <div className="summary-metrics">
                    <div><span>Questions attempted</span><strong>{summary.questions_attempted} / {summary.total_questions}</strong></div>
                    <div><span>Correct answers</span><strong>{summary.questions_correct}</strong></div>
                    <div><span>Accuracy</span><strong>{Number(summary.accuracy).toFixed(1)}%</strong></div>
                    <div><span>Hints used</span><strong>{summary.hints_used}</strong></div>
                    <div><span>Status</span><strong className="summary-status">{summary.status}</strong></div>
                  </div>
                )}
                <button
                  className="button button-primary"
                  disabled={Boolean(busyAction)}
                  onClick={() => {
                    setSession(null)
                    setEvaluation(null)
                    setSummary(null)
                    setHint('')
                    setHintLevel(0)
                    setAnswer('')
                    setError('')
                    setSummaryError('')
                  }}
                  type="button"
                >
                  Start another session
                </button>
              </div>
            </section>
          ) : evaluation ? (
            <div className="dsa-next-row">
              <p>Your progress is saved when the session is complete.</p>
              <button className="button button-primary" disabled={Boolean(busyAction)} onClick={handleNext} type="button">
                {busyAction === 'next' ? <span className="button-spinner" aria-hidden="true" /> : null}
                {busyAction === 'next' ? 'Loading question' : 'Next Question'}
                {busyAction !== 'next' && <span aria-hidden="true">→</span>}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}

export default DsaPracticePage