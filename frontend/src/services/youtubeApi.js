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


/**
 * Trim a clip and generate a new video from it.
 * @param {number} sourceId - YouTubeSource ID
 * @param {number} insightIndex - Index of the insight
 * @param {number} startTime - Trim start time in seconds
 * @param {number} endTime - Trim end time in seconds
 * @param {string} commentaryStyle - Style: reaction, analysis, or educational
 * @returns {Promise<Object>} TrimAndGenerateResponse
 */
export async function trimAndGenerate(sourceId, insightIndex, startTime, endTime, commentaryStyle = 'reaction') {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/insights/${insightIndex}/trim-and-generate`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_time: startTime,
                end_time: endTime,
                commentary_style: commentaryStyle,
                auto_approve: true
            })
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to trim and generate video');
    }

    return response.json();
}


// ═══════════════════════════════════════════════════════════════
// Phase 3: Universal Download & Editor API
// ═══════════════════════════════════════════════════════════════

/**
 * Get video metadata without downloading.
 * @param {string} url - Video URL (YouTube, X/Twitter, LinkedIn)
 * @returns {Promise<Object>} Video info (title, duration, platform, etc.)
 */
export async function getVideoInfo(url) {
    const response = await fetch(`${API_BASE}/api/youtube/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get video info');
    }

    return response.json();
}

/**
 * Download a video from any supported platform.
 * @param {string} url - Video URL (YouTube, X/Twitter, LinkedIn)
 * @param {boolean} stripAudio - Remove original audio
 * @returns {Promise<Object>} Download response with source_id, file_path, etc.
 */
export async function downloadVideo(url, stripAudio = false) {
    const response = await fetch(`${API_BASE}/api/youtube/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, strip_audio: stripAudio })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to download video');
    }

    return response.json();
}

/**
 * Get structured transcript for a source.
 * @param {number} sourceId - YouTubeSource ID
 * @returns {Promise<Object>} Transcript with segments
 */
export async function getTranscript(sourceId) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/transcript`
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get transcript');
    }

    return response.json();
}

/**
 * Get the music library (available tracks).
 * @returns {Promise<Object>} Music library with tracks list
 */
export async function getMusicLibrary() {
    const response = await fetch(`${API_BASE}/api/youtube/music-library`);

    if (!response.ok) {
        throw new Error('Failed to fetch music library');
    }

    return response.json();
}

/**
 * Generate a video using the editor pipeline (requires downloaded video).
 * @param {number} sourceId - YouTubeSource ID
 * @param {Object} options - Editor options (trim, strip audio, music, captions)
 * @returns {Promise<Object>} Editor generation response
 */
export async function editorGenerate(sourceId, options = {}) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/editor/generate`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                trim_start: options.trimStart ?? null,
                trim_end: options.trimEnd ?? null,
                strip_audio: options.stripAudio ?? true,
                music_track: options.musicTrack ?? null,
                music_volume: options.musicVolume ?? 0.12,
                generate_captions: options.generateCaptions ?? true,
                caption_source: options.captionSource ?? 'transcript',
                commentary_style: options.commentaryStyle ?? 'reaction',
                auto_approve: options.autoApprove ?? true,
                content_type: options.contentType ?? 'youtube_import'
            })
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate editor video');
    }

    return response.json();
}

/**
 * Generate a script preview from transcript/summary (no video download needed).
 * @param {number} sourceId - YouTubeSource ID
 * @param {Object} options - Script options (trim range, style, content type)
 * @returns {Promise<Object>} Script preview with scenes and catchy title
 */
export async function generateScript(sourceId, options = {}) {
    const response = await fetch(
        `${API_BASE}/api/youtube/sources/${sourceId}/generate-script`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                trim_start: options.trimStart ?? null,
                trim_end: options.trimEnd ?? null,
                strip_audio: options.stripAudio ?? true,
                music_track: options.musicTrack ?? null,
                music_volume: options.musicVolume ?? 0.12,
                generate_captions: options.generateCaptions ?? true,
                caption_source: options.captionSource ?? 'transcript',
                commentary_style: options.commentaryStyle ?? 'reaction',
                auto_approve: false,
                content_type: options.contentType ?? 'youtube_import'
            })
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate script preview');
    }

    return response.json();
}

/**
 * Approve a reviewed script and start video rendering.
 * Passes editor settings so the backend can download/edit the video.
 * @param {number} scriptId - Script ID to approve
 * @param {Object} editorSettings - Trim, audio, music settings
 * @returns {Promise<Object>} Rendering response
 */
export async function approveAndRender(scriptId, editorSettings = {}) {
    const params = new URLSearchParams({
        trim_start: editorSettings.trimStart ?? 0,
        trim_end: editorSettings.trimEnd ?? 60,
        strip_audio: editorSettings.stripAudio ?? true,
        music_volume: editorSettings.musicVolume ?? 0.12,
    });
    if (editorSettings.musicTrack) {
        params.set('music_track', editorSettings.musicTrack);
    }

    const response = await fetch(
        `${API_BASE}/api/youtube/scripts/${scriptId}/approve-and-render?${params}`,
        { method: 'POST' }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to approve and render');
    }

    return response.json();
}
