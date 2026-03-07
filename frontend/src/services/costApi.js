/**
 * Cost Tracker API Client
 *
 * Estimates Gemini/Veo API spend based on current pricing (March 2026).
 * All values are estimates — not actual Google billing amounts.
 */

import { API_BASE_URL } from '../config';

/**
 * Get per-video cost estimate for a given configuration.
 * @param {Object} params
 * @param {string} params.content_type  'book_review' | 'viral_news'
 * @param {string} params.video_source  'veo' | 'stock'
 * @param {string} params.image_source  'ai_generated' | 'stock'
 * @param {string} params.tts_provider  'openai' | 'google' | 'elevenlabs'
 */
export async function fetchCostEstimate({
    content_type = 'book_review',
    video_source = 'veo',
    image_source = 'ai_generated',
    tts_provider = 'openai',
} = {}) {
    const params = new URLSearchParams({ content_type, video_source, image_source, tts_provider });
    const response = await fetch(`${API_BASE_URL}/api/costs/estimate?${params}`);
    if (!response.ok) throw new Error(`Cost estimate failed: ${response.statusText}`);
    return response.json();
}

/**
 * Get daily spend history for the past N days.
 * @param {number} days  Number of days to look back (default 30)
 */
export async function fetchDailySpend(days = 30) {
    const params = new URLSearchParams({ days });
    const response = await fetch(`${API_BASE_URL}/api/costs/daily?${params}`);
    if (!response.ok) throw new Error(`Daily spend fetch failed: ${response.statusText}`);
    return response.json();
}

/**
 * Get pricing table for all config combinations.
 */
export async function fetchConfigOptions() {
    const response = await fetch(`${API_BASE_URL}/api/costs/config-options`);
    if (!response.ok) throw new Error(`Config options fetch failed: ${response.statusText}`);
    return response.json();
}
