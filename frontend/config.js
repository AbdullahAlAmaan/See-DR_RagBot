// Configuration file - can be customized for different environments
// In Vercel, you can set environment variables and they'll be injected here
// For now, this is a simple way to configure the API URL

// Set your API URL here
// On Vercel, use relative path /api since API routes are handled by the same domain
// For local development, use http://localhost:8000
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
window.API_URL = isProduction ? '/api' : 'http://localhost:8000';

