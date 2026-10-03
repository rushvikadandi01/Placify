import { useState } from 'react'
import MetricCard from '../components/MetricCard.jsx'
import { loadProgressSummary, ProgressApiError } from '../services/progressApi.js'

const STUDENT_ID_KEY = 'placement-copilot.studentId'

function safeCount(value) {
  return Number.isFinite(Number(value)) && Number(value) >= 0 ? Number(value) : 0
}

function DashboardPage() {
  const [studentId, setStudentId] = useState(() => localStorage.getItem(STUDENT_ID_KEY) ?? '')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [hasLoaded, setHasLoaded] = useState(false)

  async function handleLoadProgress(event) {
    event.preventDefault()
    const parsedId = Number(studentId)
    if (!Number.isInteger(parsedId) || parsedId < 1) {
      setError('Enter a valid student ID.')
      setSummary(null)
      return
    }

    setLoading(true)
    setError('')
    setHasLoaded(false)
    try {
      const data = await loadProgressSummary(parsedId)
      setSummary(data)
      setStudentId(String(parsedId))
      localStorage.setItem(STUDENT_ID_KEY, String(parsedId))
      setHasLoaded(true)
    } catch (loadError) {
      setSummary(null)
      setError(
        loadError instanceof ProgressApiError
          ? loadError.message
          : 'Something went wrong while loading progress.',
      )
    } finally {
      setLoading(false)
    }
  }

  const overallAccuracy = Math.min(safeCount(summary?.overall_accuracy), 100)
  const totalSessions = safeCount(summary?.total_sessions)
  const totalQuestions = safeCount(summary?.total_questions)
  const totalCorrect = safeCount(summary?.total_correct)
  const dsaSessions = safeCount(summary?.dsa_sessions)
  const aptitudeSessions = safeCount(summary?.aptitude_sessions)
  const interviewSessions = safeCount(summary?.interview_sessions)
  const interviewScore = summary?.average_interview_score
  const hasInterviewScore = interviewScore !== null && interviewScore !== undefined && Number.isFinite(Number(interviewScore))

  return (
    <div className="dashboard-page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">YOUR PREPARATION, ORGANIZED</p>
          <h1>Placify</h1>
          <p className="page-subtitle">Your AI-powered placement preparation companion</p>
        </div>
        <div className="heading-date">
          <span className="date-mark" aria-hidden="true">◷</span>
          <span>One session at a time</span>
        </div>
      </section>

      <section aria-labelledby="student-progress-title" className="student-panel">
        <div className="student-panel-copy">
          <span className="panel-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="8" r="3.2" />
              <path d="M5.5 20c.7-3.1 3.1-5 6.5-5s5.8 1.9 6.5 5" />
            </svg>
          </span>
          <div>
            <h2 id="student-progress-title">Your progress</h2>
            <p>Load your saved practice results to see how you’re tracking.</p>
          </div>
        </div>
        <form className="student-form" onSubmit={handleLoadProgress}>
          <label className="student-id-field" htmlFor="student-id">
            <span>Student ID</span>
            <input
              autoComplete="off"
              id="student-id"
              inputMode="numeric"
              min="1"
              onChange={(event) => setStudentId(event.target.value)}
              placeholder="e.g. 10"
              type="number"
              value={studentId}
            />
          </label>
          <button className="button button-primary load-button" disabled={loading} type="submit">
            {loading ? <span className="button-spinner" aria-hidden="true" /> : null}
            {loading ? 'Loading' : 'Load progress'}
            {!loading && <span aria-hidden="true">→</span>}
          </button>
        </form>
      </section>

      {error && (
        <div className="alert alert-error" role="alert">
          <span aria-hidden="true">!</span>
          <p>{error}</p>
        </div>
      )}

      <div className="section-heading">
        <div>
          <p className="eyebrow">AT A GLANCE</p>
          <h2>{hasLoaded ? `Student ${summary?.student_id ?? studentId}` : 'Your training overview'}</h2>
        </div>
        {hasLoaded && totalSessions > 0 && (
          <span className="loaded-badge"><span /> Progress synced</span>
        )}
      </div>

      {!hasLoaded ? (
        <section className="empty-dashboard">
          <div className="empty-illustration" aria-hidden="true">
            <span className="empty-sun" />
            <span className="empty-page"><i /><i /><i /></span>
            <span className="empty-spark">✦</span>
          </div>
          <div className="empty-copy">
            <p className="eyebrow">A CLEAR PLACE TO START</p>
            <h2>Bring your progress into view</h2>
            <p>Enter your student ID above to see your practice sessions, accuracy, and interview scores.</p>
          </div>
          <div className="empty-divider" />
          <div className="empty-next-step">
            <span className="step-number">01</span>
            <div>
              <strong>Load your progress</strong>
              <p>Your saved training results will appear here.</p>
            </div>
          </div>
        </section>
      ) : (
        <>
          {totalSessions === 0 && (
            <div className="alert alert-empty" role="status">
              <span aria-hidden="true">✳</span>
              <p>No practice history yet. Complete a DSA, aptitude, or interview session and your progress will show up here.</p>
            </div>
          )}
          <section aria-label="Training metrics" className="metrics-grid">
            <MetricCard
              accent="overall"
              detail={`${totalCorrect} correct out of ${totalQuestions} attempted`}
              icon="↗"
              label="Overall accuracy"
              progress={overallAccuracy}
              value={`${overallAccuracy.toFixed(1)}%`}
            />
            <MetricCard
              accent="dsa"
              detail={dsaSessions === 0 ? 'Ready when you are' : `${dsaSessions} completed ${dsaSessions === 1 ? 'session' : 'sessions'}`}
              icon="⌘"
              label="DSA practice"
              value={dsaSessions}
            />
            <MetricCard
              accent="aptitude"
              detail={aptitudeSessions === 0 ? 'Ready when you are' : `${aptitudeSessions} completed ${aptitudeSessions === 1 ? 'session' : 'sessions'}`}
              icon="◎"
              label="Aptitude"
              value={aptitudeSessions}
            />
            <MetricCard
              accent="interview"
              detail={hasInterviewScore ? `${Number(interviewScore).toFixed(1)} / 10 average score` : 'No interview score yet'}
              icon="“"
              label="Interview practice"
              value={interviewSessions}
            />
            <MetricCard
              accent="sessions"
              detail={`${totalQuestions} questions attempted`}
              icon="▤"
              label="Total sessions"
              value={totalSessions}
            />
          </section>

          <section className="dashboard-lower-grid">
            <article className="momentum-panel">
              <div className="panel-heading-row">
                <div>
                  <p className="eyebrow">KEEP YOUR MOMENTUM</p>
                  <h2>Your next good step</h2>
                </div>
                <span className="momentum-glyph" aria-hidden="true">↗</span>
              </div>
              <p className="momentum-copy">
                {totalSessions === 0
                  ? 'Start with a short practice session. Your dashboard will build as you go.'
                  : `You’ve completed ${totalSessions} ${totalSessions === 1 ? 'session' : 'sessions'}. Keep a steady rhythm and revisit topics as you learn.`}
              </p>
              <div className="momentum-rule"><span style={{ width: `${totalSessions ? Math.min(totalSessions * 12, 88) : 8}%` }} /></div>
              <div className="momentum-foot"><span>Practice streak</span><span>{totalSessions ? `${totalSessions} session${totalSessions === 1 ? '' : 's'} logged` : 'Your first session is waiting'}</span></div>
            </article>

            <article className="study-card">
              <div className="study-card-art" aria-hidden="true">
                <span className="art-ring art-ring-one" />
                <span className="art-ring art-ring-two" />
                <span className="art-spark">✳</span>
                <span className="art-book">↗</span>
              </div>
              <div className="study-card-content">
                <p className="eyebrow">BUILT AROUND YOUR PROGRESS</p>
                <h2>Study Plan</h2>
                <p>A practical plan can turn your next study hours into focused progress.</p>
                <span className="study-card-note">Choose “Study Plan” in the sidebar to explore this area.</span>
              </div>
            </article>
          </section>
          <p className="data-footnote">Progress reflects completed training sessions linked to this student ID.</p>
        </>
      )}
    </div>
  )
}

export default DashboardPage