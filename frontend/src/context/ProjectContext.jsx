import { createContext, useContext, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const ProjectContext = createContext(null);

// Route mapping: old view names → actual URL paths
const VIEW_TO_PATH = {
    content: '/content',
    youtube: '/youtube',
    books: '/books',
    scripts: '/scripts',
    videos: '/videos',
    validation: '/videos',  // 'validation' was an alias for 'videos'
    dashboard: '/dashboard',
};

export function useProject() {
    const context = useContext(ProjectContext);
    if (!context) {
        throw new Error('useProject must be used within a ProjectProvider');
    }
    return context;
}

export function ProjectProvider({ children }) {
    // We keep navigateTo as a compatibility shim so pages don't break
    // Pages will gradually migrate to useNavigate() directly

    const value = {
        // Compatibility shim — used by page components
        NavigateShim,
    };

    return (
        <ProjectContext.Provider value={value}>
            {children}
        </ProjectContext.Provider>
    );
}

/**
 * Hook that replaces the old navigateTo pattern.
 * Usage: const { navigateTo } = useProject();
 *        navigateTo('scripts');
 *        navigateTo('videos', { videoId: 123 });
 */
export function useAppNavigate() {
    const navigate = useNavigate();
    const navigateTo = useCallback((view, params = null) => {
        const path = VIEW_TO_PATH[view] || `/${view}`;
        if (params) {
            const searchParams = new URLSearchParams();
            Object.entries(params).forEach(([k, v]) => {
                if (v != null) searchParams.set(k, String(v));
            });
            navigate(`${path}?${searchParams.toString()}`);
        } else {
            navigate(path);
        }
    }, [navigate]);

    return { navigateTo };
}

function NavigateShim() {
    // Placeholder — actual navigation is via useAppNavigate hook
    return null;
}
