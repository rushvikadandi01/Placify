import { navigationItems } from './navigationItems.js'

function NavigationIcon({ name }) {
  const common = {
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    strokeWidth: 1.7,
    viewBox: '0 0 24 24',
    'aria-hidden': true,
  }

  const shapes = {
    dashboard: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.4" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.4" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.4" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.4" /></>,
    brackets: <><path d="M8 5H5v14h3M16 5h3v14h-3M13 8l-3 8" /><path d="M10 16h4" /></>,
    target: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.5" /><circle cx="12" cy="12" r="1" /></>,
    chat: <><path d="M20 11.4a7.4 7.4 0 0 1-7.4 7.4H7l-3.5 2v-5.1A7.4 7.4 0 1 1 20 11.4Z" /><path d="M8 11h.01M12 11h.01M16 11h.01" /></>,
    chart: <><path d="M4 19.5h16M6.5 16V11M12 16V5M17.5 16V8" /><path d="m5 8 5-3 5 2 4-3" /></>,
    calendar: <><rect x="3.5" y="5" width="17" height="15.5" rx="2" /><path d="M7.5 3.5v3M16.5 3.5v3M3.5 9h17M8 13h2M14 13h2M8 16.5h2" /></>,
  }

  return <svg {...common}>{shapes[name]}</svg>
}

function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <a className="brand-lockup" href="#dashboard" onClick={() => onNavigate('dashboard')}>
        <span className="brand-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span className="brand-name">Placify</span>
      </a>

      <div className="sidebar-label">PREPARATION</div>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {navigationItems.map((item) => (
          <button
            aria-current={activePage === item.id ? 'page' : undefined}
            className={`nav-item${activePage === item.id ? ' is-active' : ''}`}
            key={item.id}
            onClick={() => onNavigate(item.id)}
            type="button"
            title={item.label}
          >
            <NavigationIcon name={item.icon} />
            <span>{item.label}</span>
            {item.id === 'dashboard' && <span className="nav-current-dot" />}
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-note-icon" aria-hidden="true">✳</div>
        <p className="sidebar-note-title">Small steps add up.</p>
        <p className="sidebar-note-copy">A little focused practice today makes tomorrow easier.</p>
        <div className="sidebar-version">STUDENT WORKSPACE <span>•</span> 8A</div>
      </div>
    </aside>
  )
}

export default Sidebar