/**
 * Script Review API Client
 * 
 * Provides functions for interacting with script review API endpoints.
 */

import { API_BASE_URL } from '../config';

/**
 * Fetch pending scripts for review
 */
export async function fetchPendingScripts() {
    const response = await fetch(`${API_BASE_URL}/api/scripts/pending`);

    if (!response.ok) {
        throw new Error(`Failed to fetch pending scripts: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Fetch script detail with source article
 */
export async function fetchScriptDetail(scriptId) {
    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/detail`);

    if (!response.ok) {
        throw new Error(`Failed to fetch script detail: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Update script content
 */
export async function updateScriptContent(scriptId, updates) {
    const params = new URLSearchParams();

    if (updates.catchy_title) params.append('catchy_title', updates.catchy_title);
    if (updates.content_type) params.append('content_type', updates.content_type);
    if (updates.video_description) params.append('video_description', updates.video_description);
    if (updates.scenes) params.append('scenes', JSON.stringify(updates.scenes));
    if (updates.hashtags) params.append('hashtags', JSON.stringify(updates.hashtags));

    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/content?${params}`, {
        method: 'PUT',
    });

    if (!response.ok) {
        throw new Error(`Failed to update script: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Approve script (does NOT generate video)
 */
export async function approveScript(scriptId) {
    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/approve`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to approve script: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Generate video from approved script
 */
export async function generateVideo(scriptId) {
    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/generate-video`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to start video generation: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Reject script with reason
 */
export async function rejectScript(scriptId, reason) {
    const params = new URLSearchParams({ reason });

    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/reject-with-reason?${params}`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to reject script: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Regenerate script from same article
 */
export async function regenerateScript(scriptId) {
    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}/regenerate`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to regenerate script: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Delete script
 */
export async function deleteScript(scriptId) {
    const response = await fetch(`${API_BASE_URL}/api/scripts/${scriptId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error(`Failed to delete script: ${response.statusText}`);
    }
}
