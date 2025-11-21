// Configuration file - API URL configuration
// Priority: window.VERCEL_API_URL (set by vercel-env.js) > window.API_URL > default

const getApiUrl = () => {
  // Check for Vercel-injected environment variable
  if (typeof window !== 'undefined' && window.VERCEL_API_URL && window.VERCEL_API_URL !== '%API_URL%') {
    return window.VERCEL_API_URL;
  }
  
  // Check for manually set API_URL
  if (typeof window !== 'undefined' && window.API_URL) {
    return window.API_URL;
  }
  
  // For local development
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return 'http://localhost:8000';
  }
  
  // Default to Hugging Face backend URL
  return 'https://aaamaan-see-dr-ragbot.hf.space';
};

window.API_URL = getApiUrl();

