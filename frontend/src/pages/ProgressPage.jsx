import { useEffect, useState } from 'react'
import {
  loadProgressRecords,
  loadProgressSummary,
  loadTopicProgress,
  ProgressApiError,
} from '../services/progressApi'
import '../styles/progress.css'

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '—'

  return date.toLocaleDateString()
}

function formatTrainingType(type) {
  if (type === 'DSA') return 'DSA'
  if (type === 'APTITUDE') return 'Aptitude'
  if (type === 'INTERVIEW') return 'Interview'
  return type || '—'
}

function formatTopic(topic) {
  if (!topic) return '—'

  return topic
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function ProgressPage({ studentId }) {
  const [summary, setSummary] = useState(null)
  const [records, setRecords] = useState([])
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

 useEffect(() => {
  if (!studentId) {
    return
  }

    let cancelled = false

    async function loadProgress() {
      setLoading(true)
      setError('')

      try {
        const [summaryData, recordsData, topicsData] = await Promise.all([
          loadProgressSummary(studentId),
          loadProgressRecords(studentId),
          loadTopicProgress(studentId),
        ])

        if (cancelled) return

        setSummary(summaryData)
        setRecords(recordsData)
        setTopics(topicsData)
      } catch (err) {
        if (cancelled) return

        if (err instanceof ProgressApiError) {
          setError(err.message)
        } else {
          setError('Could not load progress.')
        }

        setSummary(null)
        setRecords([])
        setTopics([])
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadProgress()

    return () => {
      cancelled = true
    }
  }, [studentId])

  if (!studentId) {
    return (
      <section className="progress-page">
        <div className="progress-empty">
          <h1>Progress</h1>
          <p>
            Enter and load a student ID from the Dashboard to view your
            progress.
          </p>
        </div>
      </section>
    )
  }

  if (loading) {
    return (
      <section className="progress-page">
        <div className="progress-header">
          <div>
            <p className="page-eyebrow">PLACIFY PROGRESS</p>
            <h1>Your Progress</h1>
          </div>
        </div>

        <div className="progress-loading">
          Loading your progress...
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="progress-page">
        <div className="progress-header">
          <div>
            <p className="page-eyebrow">PLACIFY PROGRESS</p>
            <h1>Your Progress</h1>
          </div>
        </div>

        <div className="progress-error">
          <h2>Could not load progress</h2>
          <p>{error}</p>
          <p className="progress-error-hint">
            Make sure the backend is running and the student ID exists.
          </p>
        </div>
      </section>
    )
  }

  const accuracy = Number(summary?.overall_accuracy ?? 0)
  const interviewScore = summary?.average_interview_score

  return (
    <section className="progress-page">
      <div className="progress-header">
        <div>
          <p className="page-eyebrow">PLACIFY PROGRESS</p>
          <h1>Your Progress</h1>
          <p className="progress-subtitle">
            Student ID: {summary?.student_id ?? studentId}
          </p>
        </div>
      </div>

      <div className="progress-metrics">
        <div className="progress-card">
          <span>Total Sessions</span>
          <strong>{summary?.total_sessions ?? 0}</strong>
        </div>

        <div className="progress-card">
          <span>Questions Attempted</span>
          <strong>{summary?.total_questions ?? 0}</strong>
        </div>

        <div className="progress-card">
          <span>Overall Accuracy</span>
          <strong>{accuracy.toFixed(1)}%</strong>
        </div>

        <div className="progress-card">
          <span>Interview Average</span>
          <strong>
            {interviewScore == null
              ? '—'
              : Number(interviewScore).toFixed(1)}
          </strong>
        </div>
      </div>

      <div className="progress-overview-grid">
        <div className="progress-panel">
          <div className="progress-panel-header">
            <div>
              <p className="panel-eyebrow">TRAINING BREAKDOWN</p>
              <h2>Sessions by Area</h2>
            </div>
          </div>

          <div className="training-bars">
            <div className="training-row">
              <div className="training-label">
                <span>DSA</span>
                <strong>{summary?.dsa_sessions ?? 0}</strong>
              </div>

              <div className="training-track">
                <div
                  className="training-fill"
                  style={{
                    width: `${
                      summary?.total_sessions
                        ? (summary.dsa_sessions / summary.total_sessions) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div className="training-row">
              <div className="training-label">
                <span>Aptitude</span>
                <strong>{summary?.aptitude_sessions ?? 0}</strong>
              </div>

              <div className="training-track">
                <div
                  className="training-fill"
                  style={{
                    width: `${
                      summary?.total_sessions
                        ? (summary.aptitude_sessions /
                            summary.total_sessions) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <div className="training-row">
              <div className="training-label">
                <span>Interview</span>
                <strong>{summary?.interview_sessions ?? 0}</strong>
              </div>

              <div className="training-track">
                <div
                  className="training-fill"
                  style={{
                    width: `${
                      summary?.total_sessions
                        ? (summary.interview_sessions /
                            summary.total_sessions) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="progress-panel">
          <div className="progress-panel-header">
            <div>
              <p className="panel-eyebrow">ACCURACY</p>
              <h2>Overall Performance</h2>
            </div>
          </div>

          <div className="accuracy-display">
            <div
              className="accuracy-ring"
              style={{
                '--accuracy': `${Math.min(Math.max(accuracy, 0), 100)}%`,
              }}
            >
              <div>
                <strong>{accuracy.toFixed(1)}%</strong>
                <span>accuracy</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="progress-panel">
        <div className="progress-panel-header">
          <div>
            <p className="panel-eyebrow">TOPIC PERFORMANCE</p>
            <h2>Topics</h2>
          </div>
        </div>

        {topics.length === 0 ? (
          <div className="panel-empty">
            No topic-level progress available yet.
          </div>
        ) : (
          <div className="topic-table-wrapper">
            <table className="topic-table">
              <thead>
                <tr>
                  <th>Area</th>
                  <th>Topic</th>
                  <th>Attempted</th>
                  <th>Accuracy</th>
                  <th>Interview Avg.</th>
                </tr>
              </thead>

              <tbody>
                {topics.map((item, index) => (
                  <tr key={`${item.training_type}-${item.topic}-${index}`}>
                    <td>{formatTrainingType(item.training_type)}</td>
                    <td>{formatTopic(item.topic)}</td>
                    <td>{item.attempted ?? 0}</td>
                    <td>
                      {item.accuracy == null
                        ? '—'
                        : `${Number(item.accuracy).toFixed(1)}%`}
                    </td>
                    <td>
                      {item.average_score == null
                        ? '—'
                        : Number(item.average_score).toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="progress-panel">
        <div className="progress-panel-header">
          <div>
            <p className="panel-eyebrow">SESSION HISTORY</p>
            <h2>Recent Training</h2>
          </div>
        </div>

        {records.length === 0 ? (
          <div className="panel-empty">
            No training sessions recorded yet.
          </div>
        ) : (
          <div className="session-list">
            {records.map((record) => (
              <div className="session-item" key={record.id}>
                <div>
                  <strong>{formatTrainingType(record.training_type)}</strong>
                  <span>
                    {formatTopic(record.topic)}
                    {record.category ? ` · ${record.category}` : ''}
                  </span>
                </div>

                <div className="session-result">
                  {record.accuracy != null ? (
                    <strong>
                      {Number(record.accuracy).toFixed(1)}%
                    </strong>
                  ) : record.average_score != null ? (
                    <strong>
                      {Number(record.average_score).toFixed(1)}
                    </strong>
                  ) : (
                    <strong>—</strong>
                  )}

                  <span>{formatDate(record.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

export default ProgressPage