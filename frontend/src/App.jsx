import { ProjectProvider, useProject } from './context/ProjectContext';
import ContentLibrary from './pages/ContentLibrary';
import ScriptReview from './pages/ScriptReview';
import VideoValidation from './pages/VideoValidation';
import Dashboard from './pages/Dashboard';
import YouTubeImport from './pages/YouTubeImport';
import './App.css';

function MainLayout() {
  const { currentView, navigateTo, navParams } = useProject();

  return (
    <div className="app">
      <nav className="app-nav">
        <div className="nav-container">
          <h1 className="app-title">AIVideoGen</h1>
          <div className="nav-tabs">
            <button
              className={`nav-tab ${currentView === 'content' ? 'active' : ''}`}
              onClick={() => navigateTo('content')}
            >
              📚 Content Library
            </button>
            <button
              className={`nav-tab ${currentView === 'youtube' ? 'active' : ''}`}
              onClick={() => navigateTo('youtube')}
            >
              🎬 YouTube Import
            </button>
            <button
              className={`nav-tab ${currentView === 'scripts' ? 'active' : ''}`}
              onClick={() => navigateTo('scripts')}
            >
              📝 Script Review
            </button>
            <button
              className={`nav-tab ${currentView === 'videos' ? 'active' : ''}`}
              onClick={() => navigateTo('videos')}
            >
              🎥 Video Validation
            </button>
            <button
              className={`nav-tab ${currentView === 'dashboard' ? 'active' : ''}`}
              onClick={() => navigateTo('dashboard')}
            >
              📊 Dashboard
            </button>
          </div>
        </div>
      </nav>

      <main className="app-main">
        {currentView === 'content' && <ContentLibrary />}
        {currentView === 'youtube' && <YouTubeImport />}
        {currentView === 'scripts' && <ScriptReview />}
        {currentView === 'videos' && <VideoValidation initialVideoId={navParams?.videoId} />}
        {currentView === 'dashboard' && <Dashboard />}
      </main>
    </div>
  );
}

function App() {
  return (
    <ProjectProvider>
      <MainLayout />
    </ProjectProvider>
  );
}

export default App;

