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
 * Create an article from a book for video pipeline.
 */
export async function createArticleFromBook(bookId, angleIndex = 0, customAngle = null) {
    const response = await fetch(`${API_BASE}/${bookId}/create-article`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            angle_index: angleIndex,
            custom_angle: customAngle
        })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create article');
    }
    return response.json();
}

/**
 * Generate a video directly from a book (one-click flow).
 * Chains: Article → Script → TTS → Video Render.
 */
export async function generateBookVideo(bookId, angleIndex = 0, customAngle = null, projectFolder = null) {
    const body = {
        angle_index: angleIndex,
        custom_angle: customAngle
    };

    if (projectFolder) {
        body.project_folder = projectFolder;
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
