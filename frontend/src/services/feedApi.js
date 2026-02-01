/**
 * RSS Feed API Client
 * 
 * Provides functions for fetching articles from RSS feeds.
 */

import { API_BASE_URL } from '../config';

/**
 * Trigger RSS feed sync to fetch new articles
 */
export async function syncFeeds() {
    const response = await fetch(`${API_BASE_URL}/api/feeds/sync`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to sync feeds: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get list of configured RSS feeds
 */
export async function getFeeds() {
    const response = await fetch(`${API_BASE_URL}/api/feeds/`);

    if (!response.ok) {
        throw new Error(`Failed to get feeds: ${response.statusText}`);
    }

    return response.json();
}
