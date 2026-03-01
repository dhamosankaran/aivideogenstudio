/**
 * Book API service for searching and managing book reviews.
 */

const API_BASE = 'http://localhost:8000/api/books';

/**
 * Search for books by query.
 */
export async function searchBooks(query, limit = 10) {
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to search books');
    }
    return response.json();
}

/**
 * Select a book from search results to add to library.
 */
export async function selectBook(bookData) {
    const response = await fetch(`${API_BASE}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookData)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to select book');
    }
    return response.json();
}

/**
 * Get book details by ID.
 */
export async function getBook(bookId) {
    const response = await fetch(`${API_BASE}/${bookId}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get book');
    }
    return response.json();
}

/**
 * Analyze a book to extract key takeaways.
 */
export async function analyzeBook(bookId) {
    const response = await fetch(`${API_BASE}/${bookId}/analyze`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to analyze book');
    }
    return response.json();
}

/**
 * Generate a script from a book for preview before video generation.
 */
export async function generateBookScript(bookId, angleIndex = 0, customAngle = null) {
    const response = await fetch(`${API_BASE}/${bookId}/generate-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            angle_index: angleIndex,
            custom_angle: customAngle
        })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate script');
    }
    return response.json();
}

/**
 * Generate a video directly from a book (one-click flow).
 * Chains: Article → Script → TTS → Video Render.
 * Now supports reviewed script_id, tts_provider, and voice selection.
 */
export async function generateBookVideo(bookId, angleIndex = 0, customAngle = null, projectFolder = null, scriptId = null, ttsProvider = null, voice = null, backgroundMode = 'auto', imageSource = 'stock', videoSource = 'stock') {
    const body = {
        angle_index: angleIndex,
        custom_angle: customAngle,
        background_mode: backgroundMode,
        image_source: imageSource,
        video_source: videoSource
    };

    if (projectFolder) {
        body.project_folder = projectFolder;
    }
    if (scriptId) {
        body.script_id = scriptId;
    }
    if (ttsProvider) {
        body.tts_provider = ttsProvider;
    }
    if (voice) {
        body.voice = voice;
    }

    const response = await fetch(`${API_BASE}/${bookId}/generate-video`, {
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

/**
 * Prepare assets for book video (one-click asset prep).
 */
export async function prepareBookAssets(bookId) {
    const response = await fetch(`${API_BASE}/${bookId}/prepare-assets`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to prepare assets');
    }
    return response.json();
}

/**
 * Get available TTS voice options for a content type.
 */
export async function getVoiceOptions(contentType = 'book_review') {
    const response = await fetch(`${API_BASE}/voice-options?content_type=${encodeURIComponent(contentType)}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get voice options');
    }
    return response.json();
}

/**
 * Get all books in library.
 */
export async function getAllBooks(limit = 50) {
    const response = await fetch(`${API_BASE}/?limit=${limit}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get books');
    }
    return response.json();
}

