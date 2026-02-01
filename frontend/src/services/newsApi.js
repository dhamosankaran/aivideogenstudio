/**
 * NewsAPI Client
 * 
 * Provides functions for searching and importing news articles from NewsAPI.org
 */

import { API_BASE_URL } from '../config';

/**
 * Search for news articles
 */
export async function searchNews(query, options = {}) {
    const params = new URLSearchParams({
        q: query,
        ...options
    });

    const response = await fetch(`${API_BASE_URL}/api/news/search?${params}`);

    if (!response.ok) {
        throw new Error(`Failed to search news: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get top headlines
 */
export async function getTopHeadlines(options = {}) {
    const params = new URLSearchParams(options);

    const response = await fetch(`${API_BASE_URL}/api/news/headlines?${params}`);

    if (!response.ok) {
        throw new Error(`Failed to get headlines: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Import articles to database
 */
export async function importArticles(articles, sourceName = 'NewsAPI') {
    const response = await fetch(`${API_BASE_URL}/api/news/import`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            articles,
            source_name: sourceName
        }),
    });

    if (!response.ok) {
        throw new Error(`Failed to import articles: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get available news sources
 */
export async function getNewsSources(category = null, language = 'en') {
    const params = new URLSearchParams({ language });
    if (category) params.append('category', category);

    const response = await fetch(`${API_BASE_URL}/api/news/sources?${params}`);

    if (!response.ok) {
        throw new Error(`Failed to get sources: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Test NewsAPI connection
 */
export async function testNewsAPI() {
    const response = await fetch(`${API_BASE_URL}/api/news/test`);

    if (!response.ok) {
        throw new Error(`Failed to test NewsAPI: ${response.statusText}`);
    }

    return response.json();
}
