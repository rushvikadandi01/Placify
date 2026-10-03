import { useState } from 'react'
import {
  generateStudyPlan,
  StudyPlanApiError,
} from '../services/studyPlanApi.js'
import '../styles/study-plan.css'

const DEFAULT_FOCUS_AREAS = [
  'DSA',
  'Aptitude',
  'Interview',
  'Core CS',
]

function formatHours(minutes) {
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  if (hours === 0) {
    return `${remainingMinutes} min`
  }

  if (remainingMinutes === 0) {
    return `${hours} hr`
  }

  return `${hours} hr ${remainingMinutes} min`
}

function StudyPlanPage({ studentId }) {
  const [days, setDays] = useState(7)
  const [hoursPerDay, setHoursPerDay] = useState(2)
  const [focusAreas, setFocusAreas] = useState([])
  const [goal, setGoal] = useState('')

  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function toggleFocusArea(area) {
    setFocusAreas((current) =>
      current.includes(area)
        ? current.filter((item) => item !== area)
        : [...current, area]
    )
  }

  async function handleGenerate(event) {
    event.preventDefault()

    if (!studentId) {
      setError('Please load a student ID from the Dashboard first.')
      return
    }

    setLoading(true)
    setError('')
    setPlan(null)

    try {
      const data = await generateStudyPlan({
        student_id: Number(studentId),
        days: Number(days),
        hours_per_day: Number(hoursPerDay),
        focus_areas: focusAreas,
        goal: goal.trim() || null,
      })

      setPlan(data)
    } catch (err) {
      if (err instanceof StudyPlanApiError) {
        setError(err.message)
      } else {
        setError('Could not generate the study plan.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!studentId) {
    return (
      <section className="study-plan-page">
        <div className="study-plan-empty">
          <h1>Study Plan</h1>
          <p>
            Load a student ID from the Dashboard to generate a personalized
            study plan.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="study-plan-page">
      <div className="study-plan-header">
        <div>
          <p className="page-eyebrow">PERSONALIZED PREPARATION</p>
          <h1>Study Plan</h1>
          <p>
            Create a placement preparation plan based on your progress,
            strengths, and weaknesses.
          </p>
        </div>

        <div className="study-plan-student">
          Student <strong>#{studentId}</strong>
        </div>
      </div>

      <div className="study-plan-layout">
        <form className="study-plan-form" onSubmit={handleGenerate}>
          <div className="section-heading">
            <h2>Plan preferences</h2>
            <p>Tell Placify how you want to prepare.</p>
          </div>

          <div className="form-row">
            <label>
              <span>Duration</span>
              <select
                value={days}
                onChange={(event) => setDays(event.target.value)}
              >
                <option value={1}>1 day</option>
                <option value={3}>3 days</option>
                <option value={5}>5 days</option>
                <option value={7}>7 days</option>
                <option value={10}>10 days</option>
                <option value={14}>14 days</option>
                <option value={21}>21 days</option>
                <option value={30}>30 days</option>
              </select>
            </label>

            <label>
              <span>Hours per day</span>
              <input
                type="number"
                min="0.5"
                max="12"
                step="0.5"
                value={hoursPerDay}
                onChange={(event) => setHoursPerDay(event.target.value)}
              />
            </label>
          </div>

          <div className="form-section">
            <label className="form-label">Focus areas</label>

            <div className="focus-options">
              {DEFAULT_FOCUS_AREAS.map((area) => (
                <button
                  key={area}
                  type="button"
                  className={`focus-chip ${
                    focusAreas.includes(area) ? 'selected' : ''
                  }`}
                  onClick={() => toggleFocusArea(area)}
                >
                  {area}
                </button>
              ))}
            </div>

            <p className="field-hint">
              Leave these unselected to let Placify choose based on your
              progress.
            </p>
          </div>

          <label className="form-section">
            <span className="form-label">Your goal</span>
            <textarea
              rows="4"
              maxLength="300"
              placeholder="Example: Prepare for campus placements and improve my DSA and interview skills."
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
            />
          </label>

          {error && <div className="study-plan-error">{error}</div>}

          <button
            className="generate-plan-button"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Generating plan...' : 'Generate Study Plan'}
          </button>
        </form>

        <div className="study-plan-result">
          {!plan && !loading && (
            <div className="result-placeholder">
              <div className="placeholder-icon">✦</div>
              <h2>Your personalized plan will appear here</h2>
              <p>
                Generate a plan to see your daily placement preparation
                schedule.
              </p>
            </div>
          )}

          {loading && (
            <div className="result-placeholder">
              <div className="loading-spinner" />
              <h2>Building your study plan...</h2>
              <p>
                Placify is analyzing your progress and preparing your schedule.
              </p>
            </div>
          )}

          {plan && (
            <>
              <div className="plan-overview">
                <div>
                  <p className="page-eyebrow">YOUR PLAN</p>
                  <h2>{plan.overall_goal}</h2>
                  <p>{plan.progress_note}</p>
                </div>

                <div className="plan-duration">
                  <strong>{plan.duration_days}</strong>
                  <span>days</span>
                </div>
              </div>

              <div className="insight-grid">
                <div className="insight-card">
                  <span className="insight-label">Strengths</span>

                  {plan.detected_strengths?.length ? (
                    <ul>
                      {plan.detected_strengths.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No strengths detected yet.</p>
                  )}
                </div>

                <div className="insight-card">
                  <span className="insight-label">Areas to improve</span>

                  {plan.detected_weaknesses?.length ? (
                    <ul>
                      {plan.detected_weaknesses.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No major weaknesses detected yet.</p>
                  )}
                </div>
              </div>

              <div className="daily-plan-section">
                <div className="section-heading">
                  <h2>Daily schedule</h2>
                  <p>
                    {plan.hours_per_day} hours per day ·{' '}
                    {plan.duration_days} days
                  </p>
                </div>

                <div className="daily-plan-list">
                  {plan.daily_plan.map((day) => (
                    <article className="day-card" key={day.day}>
                      <div className="day-header">
                        <div>
                          <span className="day-number">DAY {day.day}</span>
                          <h3>{formatHours(day.total_minutes)}</h3>
                        </div>
                      </div>

                      <div className="task-list">
                        {day.tasks.map((task, index) => (
                          <div
                            className="study-task"
                            key={`${task.topic}-${index}`}
                          >
                            <div className="task-time">
                              {task.duration_minutes} min
                            </div>

                            <div className="task-content">
                              <div className="task-meta">
                                <span>{task.area}</span>
                              </div>

                              <h4>{task.topic}</h4>
                              <p>{task.activity}</p>

                              <div className="task-reason">
                                <strong>Why:</strong> {task.reason}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              {plan.recommendations?.length > 0 && (
                <div className="recommendations-card">
                  <div className="section-heading">
                    <h2>Recommendations</h2>
                    <p>Keep these points in mind while following your plan.</p>
                  </div>

                  <ul>
                    {plan.recommendations.map((recommendation, index) => (
                      <li key={`${recommendation}-${index}`}>
                        {recommendation}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}

export default StudyPlanPage