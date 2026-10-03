function MetricCard({ accent, label, value, detail, icon, progress }) {
  return (
    <article className={`metric-card accent-${accent}`}>
      <div className="metric-topline">
        <span className="metric-icon" aria-hidden="true">{icon}</span>
        <span className="metric-label">{label}</span>
      </div>
      <div className="metric-value">{value}</div>
      <p className="metric-detail">{detail}</p>
      {progress !== undefined && (
        <div
          aria-label={`${progress}% overall accuracy`}
          className="metric-progress-track"
          role="img"
        >
          <span style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }} />
        </div>
      )}
    </article>
  )
}

export default MetricCard