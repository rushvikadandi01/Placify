import { useState } from 'react'
import AptitudePage from './pages/AptitudePage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import DsaPracticePage from './pages/DsaPracticePage.jsx'
import InterviewPage from './pages/InterviewPage.jsx'
import Sidebar from './components/Sidebar.jsx'
import { navigationItems } from './components/navigationItems.js'
import './styles/app.css'

const STUDENT_ID_KEY = 'placement-copilot.studentId'

function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [visitedPages, setVisitedPages] = useState(() => new Set(['dashboard']))
  const [dsaStudentId, setDsaStudentId] = useState('')
  const [aptitudeStudentId, setAptitudeStudentId] = useState('')
  const [interviewStudentId, setInterviewStudentId] = useState('')
  const activeItem = navigationItems.find((item) => item.id === activePage)

  function handleNavigate(page) {
    if (page === 'dsa') {
      setDsaStudentId(localStorage.getItem(STUDENT_ID_KEY) ?? '')
    }
    if (page === 'aptitude') {
      setAptitudeStudentId(localStorage.getItem(STUDENT_ID_KEY) ?? '')
    }
    if (page === 'interview') {
      setInterviewStudentId(localStorage.getItem(STUDENT_ID_KEY) ?? '')
    }
    setActivePage(page)
    setVisitedPages((current) => (current.has(page) ? current : new Set([...current, page])))
  }

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onNavigate={handleNavigate} />
      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-divider">/</span>
            <strong>{activeItem?.label ?? 'Dashboard'}</strong>
          </div>
          <div className="topbar-status">
            <span className="status-dot" />
            <span>Preparation space</span>
          </div>
        </header>
        <div hidden={activePage !== 'dashboard'}>
          <DashboardPage />
        </div>
        {visitedPages.has('dsa') && (
          <div hidden={activePage !== 'dsa'}>
            <DsaPracticePage onNavigate={handleNavigate} selectedStudentId={dsaStudentId} />
          </div>
        )}
        {visitedPages.has('aptitude') && (
          <div hidden={activePage !== 'aptitude'}>
            <AptitudePage onNavigate={handleNavigate} selectedStudentId={aptitudeStudentId} />
          </div>
        )}
        {visitedPages.has('interview') && (
          <div hidden={activePage !== 'interview'}>
            <InterviewPage onNavigate={handleNavigate} selectedStudentId={interviewStudentId} />
          </div>
        )}
        {activePage !== 'dashboard' && activePage !== 'dsa' && activePage !== 'aptitude' && activePage !== 'interview' && (
          <section className="placeholder-page">
            <div className="placeholder-mark">{activeItem?.shortLabel ?? 'PC'}</div>
            <p className="eyebrow">PLACIFY</p>
            <h1>{activeItem?.label}</h1>
            <p>This area is ready for a later phase. Your dashboard and progress overview are available now.</p>
            <button className="button button-primary" onClick={() => setActivePage('dashboard')}>
              Back to dashboard
            </button>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
