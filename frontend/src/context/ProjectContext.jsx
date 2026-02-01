import { createContext, useState, useContext } from 'react';

const ProjectContext = createContext(null);

export function useProject() {
    const context = useContext(ProjectContext);
    if (!context) {
        throw new Error('useProject must be used within a ProjectProvider');
    }
    return context;
}

export function ProjectProvider({ children }) {
    const [currentView, setCurrentView] = useState('content');
    const [navParams, setNavParams] = useState(null);

    const navigateTo = (view, params = null) => {
        setCurrentView(view);
        setNavParams(params);
    };

    const value = {
        currentView,
        navParams,
        navigateTo
    };

    return (
        <ProjectContext.Provider value={value}>
            {children}
        </ProjectContext.Provider>
    );
}
