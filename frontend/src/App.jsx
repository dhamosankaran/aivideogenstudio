import { lazy, Suspense, useState } from 'react';
import { Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import {
  Clapperboard,
  Library,
  Youtube,
  BookOpen,
  Flame,
  FileText,
  Film,
  BarChart3,
  DollarSign,
  PanelLeftClose,
  PanelLeft,
  Newspaper,
} from 'lucide-react';
import './App.css';

// Lazy load all page components
const ContentLibrary = lazy(() => import('./pages/ContentLibrary'));
const DailyDigest = lazy(() => import('./pages/DailyDigest'));
const YouTubeImport = lazy(() => import('./pages/YouTubeImport'));
const BookReview = lazy(() => import('./pages/BookReview'));
const ViralNews = lazy(() => import('./pages/ViralNews'));
const ScriptReview = lazy(() => import('./pages/ScriptReview'));
const VideoValidation = lazy(() => import('./pages/VideoValidation'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const CostDashboard = lazy(() => import('./pages/CostDashboard'));

function LoadingFallback() {
  return (
    <div className="loading-fallback">
      <div className="spinner" />
      <span>Loading…</span>
    </div>
  );
}

const NAV_ITEMS = [
  { to: '/content', icon: Library, label: 'Content Library', section: 'content' },
  { to: '/daily-digest', icon: Newspaper, label: 'Daily Digest', section: 'content' },
  { to: '/youtube', icon: Youtube, label: 'YouTube Import', section: 'content' },
  { to: '/books', icon: BookOpen, label: 'Book Reviews', section: 'content' },
  { to: '/viral', icon: Flame, label: 'Viral News', section: 'content' },
  { to: '/scripts', icon: FileText, label: 'Script Review', section: 'create' },
  { to: '/videos', icon: Film, label: 'Video Validation', section: 'create' },
  { to: '/dashboard', icon: BarChart3, label: 'Dashboard', section: 'overview' },
  { to: '/costs', icon: DollarSign, label: 'Cost Tracker', section: 'overview' },
];

function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <ProjectProvider>
      <div className="app">
        {/* ── Sidebar ── */}
        <nav className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon">
              <Clapperboard size={20} />
            </div>
            <span className="sidebar-brand-text">AIVideoGen</span>
          </div>

          <div className="sidebar-nav">
            <span className="nav-section-label">Content</span>
            {NAV_ITEMS.filter(n => n.section === 'content').map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="nav-item-icon" size={20} />
                <span className="nav-item-label">{item.label}</span>
              </NavLink>
            ))}

            <span className="nav-section-label">Create</span>
            {NAV_ITEMS.filter(n => n.section === 'create').map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="nav-item-icon" size={20} />
                <span className="nav-item-label">{item.label}</span>
              </NavLink>
            ))}

            <span className="nav-section-label">Overview</span>
            {NAV_ITEMS.filter(n => n.section === 'overview').map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="nav-item-icon" size={20} />
                <span className="nav-item-label">{item.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="sidebar-footer">
            <button
              className="sidebar-toggle"
              onClick={() => setCollapsed(!collapsed)}
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
              <span className="sidebar-toggle-label">
                {collapsed ? '' : 'Collapse'}
              </span>
            </button>
          </div>
        </nav>

        {/* ── Main Content ── */}
        <main className="main-content">
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              <Route path="/content" element={<ContentLibrary />} />
              <Route path="/daily-digest" element={<DailyDigest />} />
              <Route path="/youtube" element={<YouTubeImport />} />
              <Route path="/books" element={<BookReview />} />
              <Route path="/viral" element={<ViralNews />} />
              <Route path="/scripts" element={<ScriptReview />} />
              <Route path="/videos" element={<VideoValidation />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/costs" element={<CostDashboard />} />
              <Route path="/" element={<Navigate to="/content" replace />} />
              <Route path="*" element={<Navigate to="/content" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </ProjectProvider>
  );
}

export default App;
