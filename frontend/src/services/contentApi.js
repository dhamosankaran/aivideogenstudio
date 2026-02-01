/**
 * Content Curation API Client
 * 
 * Provides functions for interacting with the content curation API endpoints.
 */

import { API_BASE_URL } from '../config';

/**
 * Fetch articles with filters and pagination
 */
export async function fetchArticles(filters = {}) {
    const params = new URLSearchParams();

    if (filters.source) params.append('source', filters.source);
    if (filters.date_range) params.append('date_range', filters.date_range);
    if (filters.content_type) params.append('content_type', filters.content_type);
    if (filters.status) params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);
    if (filters.page) params.append('page', filters.page);
    if (filters.page_size) params.append('page_size', filters.page_size);

    const response = await fetch(`${API_BASE_URL}/api/content/articles?${params}`);

    if (!response.ok) {
        throw new Error(`Failed to fetch articles: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get a single article by ID
 */
export async function fetchArticle(articleId) {
    const response = await fetch(`${API_BASE_URL}/api/content/articles/${articleId}`);

    if (!response.ok) {
        throw new Error(`Failed to fetch article: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Mark articles as selected
 */
export async function selectArticles(articleIds) {
    const response = await fetch(`${API_BASE_URL}/api/content/articles/select`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article_ids: articleIds }),
    });

    if (!response.ok) {
        throw new Error(`Failed to select articles: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Delete selected articles
 */
export async function deleteArticles(articleIds) {
    const response = await fetch(`${API_BASE_URL}/api/content/articles/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article_ids: articleIds }),
    });

    if (!response.ok) {
        throw new Error(`Failed to delete articles: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Generate scripts from selected articles
 */
export async function generateScripts(articleIds, contentType = 'daily_update') {
    const response = await fetch(`${API_BASE_URL}/api/content/scripts/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            article_ids: articleIds,
            content_type: contentType
        }),
    });

    if (!response.ok) {
        throw new Error(`Failed to generate scripts: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Analyze an article with AI
 */
export async function analyzeArticle(articleId) {
    const response = await fetch(`${API_BASE_URL}/api/content/articles/${articleId}/analyze`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to analyze article: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get list of available sources
 */
export async function fetchSources() {
    const response = await fetch(`${API_BASE_URL}/api/content/sources`);

    if (!response.ok) {
        throw new Error(`Failed to fetch sources: ${response.statusText}`);
    }

    const data = await response.json();
    return data.sources;
}

/**
 * Get list of available content types
 */
export async function fetchContentTypes() {
    const response = await fetch(`${API_BASE_URL}/api/content/content-types`);

    if (!response.ok) {
        throw new Error(`Failed to fetch content types: ${response.statusText}`);
    }

    const data = await response.json();
    return data.content_types;
}
