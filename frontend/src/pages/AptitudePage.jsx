import { useState } from 'react'
import {
  AptitudeApiError,
  loadAptitudeSessionSummary,
  loadNextAptitudeQuestion,
  requestAptitudeQuestion,
  startAptitudeSession,
  submitAptitudeAnswer,
  submitAptitudeSessionAnswer,
} from '../services/aptitudeApi.js'
import '../styles/aptitude.css'

const categoryOptions = [
  { value: 'QUANTITATIVE', label: 'Quantitative' },
  { value: 'LOGICAL_REASONING', label: 'Logical Reasoning' },
  { value: 'VERBAL', label: 'Verbal' },
]

const topicsByCategory = {
  QUANTITATIVE: [
    { value: 'Percentages', label: 'Percentages' },
    { value: 'Profit and Loss', label: 'Profit / Loss' },
    { value: 'Ratio and Proportion', label: 'Ratio / Proportion' },
    { value: 'Averages', label: 'Averages' },
    { value: 'Time and Work', label: 'Time / Work' },
    { value: 'Time Speed Distance', label: 'Time Speed Distance' },
    { value: 'Simple Interest', label: 'Simple Interest' },
    { value: 'Compound Interest', label: 'Compound Interest' },
    { value: 'Number System', label: 'Number System' },
  ],
  LOGICAL_REASONING: [
    { value: 'Number Series', label: 'Number Series' },
    { value: 'Coding Decoding', label: 'Coding Decoding' },
    { value: 'Blood Relations', label: 'Blood Relations' },
    { value: 'Directions', label: 'Directions' },
    { value: 'Syllogisms', label: 'Syllogisms' },
    { value: 'Seating Arrangement', label: 'Seating Arrangement' },
  ],
  VERBAL: [
    { value: 'Grammar', label: 'Grammar' },
    { value: 'Vocabulary', label: 'Vocabulary' },
    { value: 'Sentence Correction', label: 'Sentence Correction' },
    { value: 'Reading Comprehension', label: 'Reading Comprehension' },
  ],
}

const difficulties = ['Easy', 'Medium', 'Hard']
const questionCounts = [1, 3, 5, 10, 20]

function AptitudePage({ onNavigate, selectedStudentId }) {
  const [mode, setMode] = useState('single')
  const [category, setCategory] = useState('QUANTITATIVE')
  const [topic, setTopic] = useState('Percentages')
  const [difficulty, setDifficulty] = useState('Easy')
  const [totalQuestions, setTotalQuestions] = useState(3)
  const [question, setQuestion] = useState(null)
  const [session, setSession] = useState(null)
  const [evaluation, setEvaluation] = useState(null)
  const [summary, setSummary] = useState(null)
  const [selectedAnswer, setSelectedAnswer] = useState('')
  const [busyAction, setBusyAction] = useState('')
  const [error, setError] = useState('')
  const [summaryError, setSummaryError] = useState('')

  const studentNumber = Number(selectedStudentId)
  const hasStudent = Number.isInteger(studentNumber) && studentNumber > 0
  const currentQuestion = session?.question ?? question
  const sessionCompleted = evaluation?.status === 'completed' || summary?.status === 'completed'
  const topics = topicsByCategory[category]

  function resetPractice() {
    setQuestion(null)
    setSession(null)
    setEvaluation(null)
    setSummary(null)
    setSelectedAnswer('')
    setError('')
    setSummaryError('')
  }

  function handleCategoryChange(value) {
    setCategory(value)
    setTopic(topicsByCategory[value][0].value)
  }

  async function handleStart(event) {
    event.preventDefault()
    resetPractice()
    setBusyAction('start')
    try {
      if (mode === 'session') {
        setSession(await startAptitudeSession({
          category,
          topic,
          difficulty,
          totalQuestions,
          studentId: studentNumber,
        }))
      } else {
        setQuestion(await requestAptitudeQuestion({ category, topic, difficulty }))
      }
    } catch (startError) {
      setError(startError instanceof AptitudeApiError ? startError.message : 'Could not start aptitude practice.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!currentQuestion || !selectedAnswer) {
      setError('Select one of the four options before submitting.')
      return
    }
    setBusyAction('submit')
    setError('')
    try {
      const result = session
        ? await submitAptitudeSessionAnswer(session.session_id, currentQuestion.question_id, selectedAnswer)
        : await submitAptitudeAnswer(currentQuestion.question_id, selectedAnswer)
      setEvaluation(result)
      if (session && result.status === 'completed') {
        try {
          setSummary(await loadAptitudeSessionSummary(session.session_id))
        } catch (summaryLoadError) {
          setSummaryError(summaryLoadError instanceof AptitudeApiError ? summaryLoadError.message : 'Could not load the completed session summary.')
        }
      }
    } catch (submitError) {
      setError(submitError instanceof AptitudeApiError ? submitError.message : 'Could not submit this answer.')
    } finally {
      setBusyAction('')
    }
  }

  async function handleNext() {
    if (!session || sessionCompleted) return
    setBusyAction('next')
    setError('')
    try {
      setSession(await loadNextAptitudeQuestion(session.session_id))
      setEvaluation(null)
      setSelectedAnswer('')
    } catch (nextError) {
      setError(nextError instanceof AptitudeApiError ? nextError.message : 'Could not load the next question.')
    } finally {
      setBusyAction('')
    }
  }

  function renderError(message) {
    return (
      <div className="alert alert-error aptitude-alert" role="alert">
        <span aria-hidden="true">!</span>
        <p>{message}</p>
      </div>
    )
  }

  return (
    <div className="dashboard-page aptitude-page">
      <section className="page-heading aptitude-page-heading">
        <div>
          <p className="eyebrow">PRACTICE WITH INTENTION</p>
          <h1>Aptitude Practice</h1>
          <p className="page-subtitle">Build speed and confidence one question at a time.</p>
        </div>
        <span className="aptitude-heading-mark" aria-hidden="true">◎</span>
      </section>

      {!hasStudent && mode === 'session' && (
        <div className="student-required-note" role="status">
          <span className="student-required-icon" aria-hidden="true">i</span>
          <div>
            <strong>Choose a student first</strong>
            <p>Load a student ID on the Dashboard to link this session to their progress.</p>
          </div>
          <button className="button button-secondary" onClick={() => onNavigate('dashboard')} type="button">
            Go to Dashboard
          </button>
        </div>
      )}

      {!currentQuestion ? (
        <section className="aptitude-setup-card">
          <div className="aptitude-mode-control" aria-label="Practice mode" role="group">
            <button aria-pressed={mode === 'single'} className={mode === 'single' ? 'is-selected' : ''} onClick={() => setMode('single')} type="button">Single question</button>
            <button aria-pressed={mode === 'session'} className={mode === 'session' ? 'is-selected' : ''} onClick={() => setMode('session')} type="button">Practice session</button>
          </div>

          <div className="aptitude-setup-intro">
            <div className="aptitude-section-icon" aria-hidden="true">01</div>
            <div>
              <p className="eyebrow">SESSION SETUP</p>
              <h2>{mode === 'single' ? 'Choose a question' : 'Build a practice set'}</h2>
              <p>Select a category, topic, and difficulty to get started.</p>
            </div>
          </div>

          <form onSubmit={handleStart}>
            <div className="aptitude-select-grid">
              <label className="aptitude-field" htmlFor="aptitude-category">
                <span>Category</span>
                <select id="aptitude-category" onChange={(event) => handleCategoryChange(event.target.value)} value={category}>
                  {categoryOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>
              <label className="aptitude-field" htmlFor="aptitude-topic">
                <span>Topic</span>
                <select id="aptitude-topic" onChange={(event) => setTopic(event.target.value)} value={topic}>
                  {topics.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
              </label>
              <label className="aptitude-field" htmlFor="aptitude-difficulty">
                <span>Difficulty</span>
                <select id="aptitude-difficulty" onChange={(event) => setDifficulty(event.target.value)} value={difficulty}>
                  {difficulties.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              {mode === 'session' && (
                <label className="aptitude-field" htmlFor="aptitude-count">
                  <span>Questions</span>
                  <select id="aptitude-count" onChange={(event) => setTotalQuestions(Number(event.target.value))} value={totalQuestions}>
                    {questionCounts.map((item) => <option key={item} value={item}>{item} {item === 1 ? 'question' : 'questions'}</option>)}
                  </select>
                </label>
              )}
            </div>
            {error && renderError(error)}
            <div className="aptitude-start-row">
              <p>{mode === 'single' ? 'The answer stays hidden until you submit.' : 'Questions arrive one at a time. Your session is saved with your student ID.'}</p>
              <button className="button button-primary aptitude-start-button" disabled={Boolean(busyAction) || (mode === 'session' && !hasStudent)} type="submit">
                {busyAction === 'start' ? <span className="button-spinner" aria-hidden="true" /> : null}
                {busyAction === 'start' ? 'Preparing question' : mode === 'single' ? 'Get Question' : 'Start Practice'}
                {busyAction !== 'start' && <span aria-hidden="true">→</span>}
              </button>
            </div>
          </form>
        </section>
      ) : (
        <>
          <div className="aptitude-session-strip">
            <div className="aptitude-session-meta">
              <span className="aptitude-category-chip">{categoryOptions.find((item) => item.value === currentQuestion.category)?.label ?? currentQuestion.category}</span>
              <span className="aptitude-topic-chip">{currentQuestion.topic}</span>
              <span className={`aptitude-difficulty-chip difficulty-${currentQuestion.difficulty.toLowerCase()}`}>{currentQuestion.difficulty}</span>
              {session && <span className="aptitude-question-count">Question {session.question_number} of {session.total_questions}</span>}
            </div>
            {!sessionCompleted && (
              <button className="text-button" disabled={Boolean(busyAction)} onClick={resetPractice} type="button">End practice</button>
            )}
          </div>

          {error && renderError(error)}

          <section className="aptitude-question-card">
            <div className="aptitude-question-heading">
              <div>
                <p className="eyebrow">{session ? `QUESTION ${String(session.question_number).padStart(2, '0')}` : 'YOUR QUESTION'}</p>
                <h2>Take a moment to think it through.</h2>
              </div>
              <span className="aptitude-question-mark" aria-hidden="true">?</span>
            </div>
            <p className="aptitude-question-text">{currentQuestion.question}</p>

            <form onSubmit={handleSubmit}>
              <fieldset className="aptitude-options" disabled={Boolean(evaluation) || Boolean(busyAction)}>
                <legend>Choose one answer</legend>
                {currentQuestion.options.map((option, index) => (
                  <label className={`aptitude-option${selectedAnswer === option ? ' is-selected' : ''}`} key={`${currentQuestion.question_id}-${index}`}>
                    <input
                      checked={selectedAnswer === option}
                      name="aptitude-answer"
                      onChange={() => setSelectedAnswer(option)}
                      type="radio"
                      value={option}
                    />
                    <span className="aptitude-option-letter">{String.fromCharCode(65 + index)}</span>
                    <span className="aptitude-option-text">{option}</span>
                  </label>
                ))}
              </fieldset>
              {!evaluation && (
                <div className="aptitude-submit-row">
                  {busyAction === 'submit' && <span className="aptitude-inline-loading">Checking your answer…</span>}
                  {busyAction !== 'submit' && <span className="aptitude-inline-loading">The answer is revealed after submission.</span>}
                  <button className="button button-primary" disabled={Boolean(busyAction) || !selectedAnswer} type="submit">
                    {busyAction === 'submit' ? <span className="button-spinner" aria-hidden="true" /> : null}
                    {busyAction === 'submit' ? 'Checking answer' : 'Submit Answer'}
                    {busyAction !== 'submit' && <span aria-hidden="true">→</span>}
                  </button>
                </div>
              )}
            </form>
          </section>

          {evaluation && (
            <section className={`aptitude-result-card${evaluation.is_correct ? ' result-correct' : ' result-incorrect'}`}>
              <div className="aptitude-result-heading">
                <span className="aptitude-result-symbol" aria-hidden="true">{evaluation.is_correct ? '✓' : '↗'}</span>
                <div>
                  <p className="eyebrow">{evaluation.is_correct ? 'CORRECT' : 'KEEP LEARNING'}</p>
                  <h2>{evaluation.is_correct ? 'That’s right.' : 'Not quite this time.'}</h2>
                </div>
              </div>
              <div className="aptitude-answer-reveal">
                <span>Your answer</span><strong>{evaluation.selected_answer}</strong>
                <span>Correct answer</span><strong>{evaluation.correct_answer}</strong>
              </div>
              <div className="aptitude-explanation">
                <h3>Explanation</h3>
                <p>{evaluation.explanation}</p>
                <h3>Learning feedback</h3>
                <p>{evaluation.learning_feedback}</p>
                {evaluation.improvement_tip && <p className="aptitude-tip"><strong>Tip</strong>{evaluation.improvement_tip}</p>}
              </div>
            </section>
          )}

          {sessionCompleted ? (
            <section className="aptitude-summary-card">
              <div className="aptitude-summary-check" aria-hidden="true">✓</div>
              <div className="aptitude-summary-main">
                <p className="eyebrow">SESSION COMPLETE</p>
                <h2>Your practice is logged.</h2>
                {summaryError && <p className="aptitude-summary-warning">{summaryError}</p>}
                {summary && (
                  <div className="aptitude-summary-metrics">
                    <div><span>Questions attempted</span><strong>{summary.questions_attempted} / {summary.total_questions}</strong></div>
                    <div><span>Correct answers</span><strong>{summary.questions_correct}</strong></div>
                    <div><span>Accuracy</span><strong>{Number(summary.accuracy).toFixed(1)}%</strong></div>
                    <div><span>Status</span><strong className="aptitude-summary-status">{summary.status}</strong></div>
                  </div>
                )}
                <button className="button button-primary" onClick={resetPractice} type="button">Practice another set</button>
              </div>
            </section>
          ) : evaluation && session ? (
            <div className="aptitude-next-row">
              <p>Your session advances after each submitted answer.</p>
              <button className="button button-primary" disabled={Boolean(busyAction)} onClick={handleNext} type="button">
                {busyAction === 'next' ? <span className="button-spinner" aria-hidden="true" /> : null}
                {busyAction === 'next' ? 'Loading question' : 'Next Question'}
                {busyAction !== 'next' && <span aria-hidden="true">→</span>}
              </button>
            </div>
          ) : evaluation ? (
            <div className="aptitude-next-row single-question-next">
              <p>Ready for another one?</p>
              <button className="button button-primary" onClick={resetPractice} type="button">Try another question</button>
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}

export default AptitudePage