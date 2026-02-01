/**
 * YouTube API service for transcript analysis.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Submit a YouTube URL for analysis.
 * @param {string} youtubeUrl - Full YouTube URL
 * @returns {Promise<Object>} YouTubeSource data
 */
export async function analyzeYouTubeVideo(youtubeUrl) {
    const response = await fetch(`${API_BASE}/api/youtube/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: youtubeUrl })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to analyze video');
    }

    return response.json();
}

/**
 * Get all analyzed YouTube sources.
 * @param {number} limit - Maximum number of results
 * @returns {Promise<Array>} List of YouTubeSource objects
 */
export async function getYouTubeSources(limit = 50) {
    const response = await fetch(`${API_BASE}/api/youtube/sources?limit=${limit}`);

    if (!response.ok) {
        throw new Error('Failed to fetch YouTube sources');
    }

    return response.json();
}

/**
 * Get a YouTube source with its insights.
 * @param {number} sourceId - YouTubeSource ID
 * @returns {Promise<Object>} YouTubeSource with insights
 */
export async function getYouTubeSource(sourceId) {
    const response = await fetch(`${API_BASE}/api/youtube/sources/${sourceId}`);

    if (!response.ok) {
        throw new Error('Failed to fetch YouTube source');
    }

    return response.json();
}

/**
 * Create a Short from an insight.
 * @param {number} sourceId - YouTubeSource ID
 * @param {number} insightIndex - Index of the insight
 * @param {string} mode - "A" for clip+commentary, "B" for original
 * @returns {Promise<Object>} Created article data
 */
export async function createShortFromInsight(sourceId, insightIndex, mode) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/insights/${insightIndex}/create-short`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, content_type: 'daily_update' })
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create short');
    }

    return response.json();
}

/**
 * Trigger re-analysis of a YouTube source.
 * @param {number} sourceId - YouTubeSource ID
 * @returns {Promise<Object>} Updated YouTubeSource
 */
export async function reanalyzeSource(sourceId) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/reanalyze`,
        { method: 'POST' }
    );

    if (!response.ok) {
        throw new Error('Failed to reanalyze source');
    }

    return response.json();
}

/**
 * Get the full video summary.
 * @param {number} sourceId - YouTubeSource ID
 * @returns {Promise<Object>} Video summary data
 */
export async function getVideoSummary(sourceId) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/summary`
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get video summary');
    }

    return response.json();
}

/**
 * Generate Mode A (Clip + Commentary) video.
 * @param {number} sourceId - YouTubeSource ID
 * @param {number} insightIndex - Index of the insight
 * @param {Object} options - Generation options
 * @returns {Promise<Object>} Mode A generation response
 */
export async function generateModeA(sourceId, insightIndex, options = {}) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/insights/${insightIndex}/generate-mode-a`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                commentary_style: options.commentaryStyle || 'reaction',
                auto_approve: options.autoApprove !== false
            })
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate Mode A video');
    }

    return response.json();
}

/**
 * Generate Mode B (Original Content) article and script.
 * @param {number} sourceId - YouTubeSource ID
 * @param {number} insightIndex - Index of the insight
 * @param {Object} options - Generation options
 * @returns {Promise<Object>} Mode B generation response
 */
export async function generateModeB(sourceId, insightIndex, options = {}) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/insights/${insightIndex}/generate-mode-b`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content_type: options.contentType || 'daily_update'
            })
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate Mode B content');
    }

    return response.json();
}

