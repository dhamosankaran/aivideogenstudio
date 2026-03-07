/**
 * Viral News API service for discovering and managing viral news sources.
 */

const API_BASE = 'http://localhost:8000/api/viral-news';

/**
 * Discover trending news articles.
 */
export async function discoverTrending(category = null, query = null, pageSize = 15) {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (query) params.set('query', query);
    params.set('page_size', pageSize);

    const response = await fetch(`${API_BASE}/trending?${params}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to discover trending news');
    }
    return response.json();
}

/**
 * Save a trending article as a viral news source.
 */
export async function saveSource(articleData) {
    const response = await fetch(`${API_BASE}/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(articleData)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save source');
    }
    return response.json();
}

/**
 * Get all saved viral news sources.
 */
export async function listSources(limit = 50, status = null) {
    const params = new URLSearchParams({ limit });
    if (status) params.set('status', status);

    const response = await fetch(`${API_BASE}/sources?${params}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to list sources');
    }
    return response.json();
}

/**
 * Get a single viral news source by ID.
 */
export async function getSource(sourceId) {
    const response = await fetch(`${API_BASE}/sources/${sourceId}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get source');
    }
    return response.json();
}

/**
 * Analyze a source for virality using LLM.
 */
export async function analyzeSource(sourceId) {
    const response = await fetch(`${API_BASE}/sources/${sourceId}/analyze`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to analyze source');
    }
    return response.json();
}

/**
 * Create an Article from a viral news source.
 */
export async function createArticle(sourceId, angleIndex = 0, customAngle = null) {
    const response = await fetch(`${API_BASE}/sources/${sourceId}/create-article`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ angle_index: angleIndex, custom_angle: customAngle })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create article');
    }
    return response.json();
}

/**
 * Generate a script from a viral news source for preview.
 * Named alias used by ViralNews.jsx
 */
export async function generateViralNewsScript(sourceId, angleIndex = 0, customAngle = null, videoDuration = '60s') {
    const response = await fetch(`${API_BASE}/sources/${sourceId}/generate-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ angle_index: angleIndex, custom_angle: customAngle, video_duration: videoDuration })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate script');
    }
    return response.json();
}
// Legacy alias
export const generateScript = generateViralNewsScript;

/**
 * Generate a video from a viral news source.
 * Positional args used by ViralNews.jsx
 */
export async function generateViralNewsVideo(
    sourceId,
    angleIndex = 0,
    customAngle = null,
    scriptId = null,
    ttsProvider = 'openai',
    voice = null,
    backgroundMode = 'auto',
    imageSource = 'stock',
    videoSource = 'stock',
    videoDuration = '60s',
) {
    const body = {
        angle_index: angleIndex,
        custom_angle: customAngle,
        script_id: scriptId,
        tts_provider: ttsProvider,
        voice: voice,
        background_mode: backgroundMode,
        image_source: imageSource,
        video_source: videoSource,
        video_duration: videoDuration,
    };

    const response = await fetch(`${API_BASE}/sources/${sourceId}/generate-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate video');
    }
    return response.json();
}
// Legacy alias (options-object form)
export async function generateVideo(sourceId, options = {}) {
    return generateViralNewsVideo(
        sourceId,
        options.angleIndex || 0,
        options.customAngle || null,
        options.scriptId || null,
        options.ttsProvider || 'openai',
        options.voice || null,
        options.backgroundMode || 'auto',
        options.imageSource || 'stock',
    );
}

/**
 * Get available TTS voice options.
 */
export async function getVoiceOptions(contentType = 'viral_news') {
    const response = await fetch(`${API_BASE}/voice-options?content_type=${encodeURIComponent(contentType)}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get voice options');
    }
    return response.json();
}

