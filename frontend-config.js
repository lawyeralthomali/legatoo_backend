// Frontend Configuration for Production
// This file provides the correct backend URL for authentication

const config = {
  // Production Backend URL (New Domain)
  BACKEND_URL: 'https://api.fastestfranchise.net',
  API_BASE_URL: 'https://api.fastestfranchise.net/api/v1',
  
  // Authentication Endpoints
  AUTH_ENDPOINTS: {
    LOGIN: 'https://api.fastestfranchise.net/api/v1/auth/login',
    SIGNUP: 'https://api.fastestfranchise.net/api/v1/auth/signup',
    REFRESH_TOKEN: 'https://api.fastestfranchise.net/api/v1/auth/refresh-token',
    LOGOUT: 'https://api.fastestfranchise.net/api/v1/auth/logout',
    FORGOT_PASSWORD: 'https://api.fastestfranchise.net/api/v1/auth/forgot-password',
    CONFIRM_PASSWORD_RESET: 'https://api.fastestfranchise.net/api/v1/auth/confirm-password-reset',
    VERIFY_EMAIL: 'https://api.fastestfranchise.net/api/v1/auth/verify-email'
  },
  
  // User Management Endpoints
  USER_ENDPOINTS: {
    PROFILE: 'https://api.fastestfranchise.net/api/v1/profiles/me',
    USERS: 'https://api.fastestfranchise.net/api/v1/users',
    SEARCH_USERS: 'https://api.fastestfranchise.net/api/v1/users/search'
  },
  
  // Contract Management Endpoints
  CONTRACT_ENDPOINTS: {
    CATEGORIES: 'https://api.fastestfranchise.net/api/contracts/categories',
    TEMPLATES: 'https://api.fastestfranchise.net/api/contracts/templates',
    USER_CONTRACTS: 'https://api.fastestfranchise.net/api/v1/user-contracts',
    FAVORITES: 'https://api.fastestfranchise.net/api/v1/favorites'
  },
  
  // Legal Assistant Endpoints (Updated for new implementation)
  LEGAL_ASSISTANT_ENDPOINTS: {
    UPLOAD: 'https://api.fastestfranchise.net/api/v1/legal-assistant/documents/upload',
    SEARCH: 'https://api.fastestfranchise.net/api/v1/legal-assistant/documents/search',
    DOCUMENTS: 'https://api.fastestfranchise.net/api/v1/legal-assistant/documents',
    STATISTICS: 'https://api.fastestfranchise.net/api/v1/legal-assistant/statistics'
  },
  
  // Subscription & Premium Endpoints
  SUBSCRIPTION_ENDPOINTS: {
    STATUS: 'https://api.fastestfranchise.net/api/v1/subscriptions/status',
    PLANS: 'https://api.fastestfranchise.net/api/v1/subscriptions/plans',
    PREMIUM_STATUS: 'https://api.fastestfranchise.net/api/v1/premium/status',
    FEATURE_LIMITS: 'https://api.fastestfranchise.net/api/v1/premium/feature-limits'
  },
  
  // Enjaz Integration Endpoints
  ENJAZ_ENDPOINTS: {
    CONNECT: 'https://api.fastestfranchise.net/api/v1/enjaz/connect',
    SYNC_CASES: 'https://api.fastestfranchise.net/api/v1/enjaz/sync-cases',
    CASES: 'https://api.fastestfranchise.net/api/v1/enjaz/cases'
  },
  
  // Frontend URLs
  FRONTEND_URLS: {
    LOGIN: 'https://legatoo.fastestfranchise.net/auth/login',
    SIGNUP: 'https://legatoo.fastestfranchise.net/auth/signup',
    DASHBOARD: 'https://legatoo.fastestfranchise.net/dashboard',
    EMAIL_VERIFICATION: 'https://legatoo.fastestfranchise.net/email-verification.html',
    PASSWORD_RESET: 'https://legatoo.fastestfranchise.net/password-reset.html'
  }
};

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = config;
} else if (typeof window !== 'undefined') {
  window.APP_CONFIG = config;
}

// For ES6 modules
export default config;
