/**
 * Video Validation API Client
 * 
 * Provides functions for interacting with video validation API endpoints.
 */

import { API_BASE_URL } from '../config';

/**
 * Fetch pending videos for validation
 */
export async function fetchPendingVideos() {
    const response = await fetch(`${API_BASE_URL}/api/video/pending`);

    if (!response.ok) {
        throw new Error(`Failed to fetch pending videos: ${response.statusText}`);
    }

    const data = await response.json();
    return data.videos;
}

/**
 * Fetch video detail with metadata
 */
export async function fetchVideoDetail(videoId) {
    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/detail`);

    if (!response.ok) {
        throw new Error(`Failed to fetch video detail: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Update video metadata
 */
export async function updateVideoMetadata(videoId, metadata) {
    const params = new URLSearchParams();

    if (metadata.youtube_title) params.append('youtube_title', metadata.youtube_title);
    if (metadata.youtube_description) params.append('youtube_description', metadata.youtube_description);
    if (metadata.hashtags) params.append('hashtags', JSON.stringify(metadata.hashtags));

    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/metadata?${params}`, {
        method: 'PUT',
    });

    if (!response.ok) {
        throw new Error(`Failed to update video metadata: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Approve video for upload
 */
export async function approveVideo(videoId) {
    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/approve`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to approve video: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Reject video with reason
 */
export async function rejectVideo(videoId, reason) {
    const params = new URLSearchParams({ reason });

    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/reject?${params}`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to reject video: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get video file URL for playback
 */
export function getVideoUrl(videoId) {
    return `${API_BASE_URL}/api/video/${videoId}/download`;
}

/**
 * Generate SEO-optimized metadata using LLM
 */
export async function generateMetadata(videoId) {
    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/generate-metadata`, {
        method: 'POST',
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Failed to generate metadata: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Generate AI thumbnail using Gemini (NanaBanana)
 */
export async function generateThumbnail(videoId, customPrompt = null) {
    const params = new URLSearchParams();
    if (customPrompt) {
        params.append('custom_prompt', customPrompt);
    }

    const url = customPrompt
        ? `${API_BASE_URL}/api/video/${videoId}/generate-thumbnail?${params}`
        : `${API_BASE_URL}/api/video/${videoId}/generate-thumbnail`;

    const response = await fetch(url, {
        method: 'POST',
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Failed to generate thumbnail: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get thumbnail prompt for preview/editing
 */
export async function getThumbnailPrompt(videoId) {
    const response = await fetch(`${API_BASE_URL}/api/video/${videoId}/thumbnail-prompt`);

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Failed to get thumbnail prompt: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get thumbnail URL for display
 */
export function getThumbnailUrl(thumbnailPath) {
    if (!thumbnailPath) return null;
    // If it's already a full URL, return as-is
    if (thumbnailPath.startsWith('http')) return thumbnailPath;
    // Otherwise, construct the static file URL
    return `${API_BASE_URL}/static/${thumbnailPath}`;
}

