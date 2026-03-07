/**
 * Daily AI Digest API service.
 *
 * Endpoints:
 *   POST /api/daily-digest/rank              — LLM-rank selected articles
 *   POST /api/daily-digest/articles          — Create digest article
 *   GET  /api/daily-digest/articles          — List existing digests
 *   POST /api/daily-digest/articles/:id/script — Generate roundup script
 *   POST /api/daily-digest/articles/:id/video  — Generate video
 *   GET  /api/daily-digest/voice-options     — TTS voice options
 */

const API_BASE = 'http://localhost:8000/api/daily-digest';
const CONTENT_BASE = 'http://localhost:8000/api/content';

// ── Content Library ────────────────────────────────────────────────

/**
 * Fetch articles from the content library.
 * Used to populate the article picker in Step 1.
 */
export async function fetchContentArticles({
    dateRange = 'today',
    source = null,
    search = null,
    page = 1,
    pageSize = 50,
} = {}) {
    const params = new URLSearchParams({ date_range: dateRange, page, page_size: pageSize });
    if (source) params.set('source', source);
    if (search) params.set('search', search);

    const response = await fetch(`${CONTENT_BASE}/articles?${params}`);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to fetch articles');
    }
    return response.json();
}

// ── Ranking ────────────────────────────────────────────────────────

/**
 * Rank selected article IDs by AI impact and relevance.
 * Returns sorted list with rank_reason, company, key_fact, impact.
 */
export async function rankArticles(articleIds) {
    const response = await fetch(`${API_BASE}/rank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_ids: articleIds }),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Ranking failed');
    }
    return response.json();
}

// ── Digest Article ─────────────────────────────────────────────────

/**
 * Create a digest article from a ranked list of article IDs.
 * Returns { article_id, title, story_count, message }.
 */
export async function createDigestArticle(rankedArticleIds, title, rankedMetadata = null) {
    const response = await fetch(`${API_BASE}/articles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ranked_article_ids: rankedArticleIds,
            title,
            ranked_metadata: rankedMetadata,
        }),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to create digest');
    }
    return response.json();
}

/**
 * List existing digest articles.
 */
export async function listDigestArticles(limit = 20) {
    const response = await fetch(`${API_BASE}/articles?limit=${limit}`);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to list digests');
    }
    return response.json();
}

// ── Script ────────────────────────────────────────────────────────

/**
 * Generate a roundup script for a digest article.
 * videoDuration: "60s" (3 stories) or "90s" (5 stories)
 */
export async function generateDigestScript(articleId, videoDuration = '60s') {
    const response = await fetch(`${API_BASE}/articles/${articleId}/script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_duration: videoDuration }),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Script generation failed');
    }
    return response.json();
}

// ── Video ─────────────────────────────────────────────────────────

/**
 * Generate a video from a digest article.
 */
export async function generateDigestVideo(
    articleId,
    {
        scriptId = null,
        ttsProvider = 'openai',
        voice = null,
        backgroundMode = 'auto',
        imageSource = 'ai_generated',
        videoSource = 'stock',
        videoDuration = '60s',
        veoStyle = 'auto',
    } = {}
) {
    const response = await fetch(`${API_BASE}/articles/${articleId}/video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            script_id: scriptId,
            tts_provider: ttsProvider,
            voice,
            background_mode: backgroundMode,
            image_source: imageSource,
            video_source: videoSource,
            video_duration: videoDuration,
            veo_style: veoStyle,
        }),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Video generation failed');
    }
    return response.json();
}

// ── Voice Options ─────────────────────────────────────────────────

/**
 * Get TTS voice options for daily_update content type.
 */
export async function getVoiceOptions(contentType = 'daily_update') {
    const response = await fetch(
        `${API_BASE}/voice-options?content_type=${encodeURIComponent(contentType)}`
    );
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to get voice options');
    }
    return response.json();
}
