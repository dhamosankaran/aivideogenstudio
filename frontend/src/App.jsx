import { lazy, Suspense, useState } from 'react';
import { Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import {
  Zap,
  Library,
  Youtube,
  BookOpen,
  FileText,
  Film,
  BarChart3,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import './App.css';

// Lazy load all page components
const ContentLibrary = lazy(() => import('./pages/ContentLibrary'));
const YouTubeImport = lazy(() => import('./pages/YouTubeImport'));
const BookReview = lazy(() => import('./pages/BookReview'));
const ScriptReview = lazy(() => import('./pages/ScriptReview'));
const VideoValidation = lazy(() => import('./pages/VideoValidation'));
const Dashboard = lazy(() => import('./pages/Dashboard'));

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
  { to: '/youtube', icon: Youtube, label: 'YouTube Import', section: 'content' },
  { to: '/books', icon: BookOpen, label: 'Book Reviews', section: 'content' },
  { to: '/scripts', icon: FileText, label: 'Script Review', section: 'create' },
  { to: '/videos', icon: Film, label: 'Video Validation', section: 'create' },
  { to: '/dashboard', icon: BarChart3, label: 'Dashboard', section: 'overview' },
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
              <Zap size={18} />
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
              <Route path="/youtube" element={<YouTubeImport />} />
              <Route path="/books" element={<BookReview />} />
              <Route path="/scripts" element={<ScriptReview />} />
              <Route path="/videos" element={<VideoValidation />} />
              <Route path="/dashboard" element={<Dashboard />} />
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
