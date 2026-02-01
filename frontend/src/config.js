/**
 * Frontend configuration
 * 
 * Uses environment variables for production flexibility.
 * Falls back to localhost for development.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
