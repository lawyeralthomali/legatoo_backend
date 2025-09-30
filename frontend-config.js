// Frontend Configuration for Production
// This file provides the correct backend URL for authentication

const config = {
  // Production Backend URL
  BACKEND_URL: 'http://srv1022733.hstgr.cloud:8000',
  API_BASE_URL: 'http://srv1022733.hstgr.cloud:8000/api/v1',
  
  // Authentication Endpoints
  AUTH_ENDPOINTS: {
    LOGIN: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/login',
    SIGNUP: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/signup',
    REFRESH_TOKEN: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/refresh-token',
    LOGOUT: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/logout',
    FORGOT_PASSWORD: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/forgot-password',
    CONFIRM_PASSWORD_RESET: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/confirm-password-reset',
    VERIFY_EMAIL: 'http://srv1022733.hstgr.cloud:8000/api/v1/auth/verify-email'
  },
  
  // User Management Endpoints
  USER_ENDPOINTS: {
    PROFILE: 'http://srv1022733.hstgr.cloud:8000/api/v1/profiles/me',
    USERS: 'http://srv1022733.hstgr.cloud:8000/api/v1/users',
    SEARCH_USERS: 'http://srv1022733.hstgr.cloud:8000/api/v1/users/search'
  },
  
  // Contract Management Endpoints
  CONTRACT_ENDPOINTS: {
    CATEGORIES: 'http://srv1022733.hstgr.cloud:8000/api/contracts/categories',
    TEMPLATES: 'http://srv1022733.hstgr.cloud:8000/api/contracts/templates',
    USER_CONTRACTS: 'http://srv1022733.hstgr.cloud:8000/api/v1/user-contracts',
    FAVORITES: 'http://srv1022733.hstgr.cloud:8000/api/v1/favorites'
  },
  
  // Legal Assistant Endpoints
  LEGAL_ASSISTANT_ENDPOINTS: {
    CHAT: 'http://srv1022733.hstgr.cloud:8000/api/v1/legal-assistant/chat',
    STATUS: 'http://srv1022733.hstgr.cloud:8000/api/v1/legal-assistant/status',
    DETECT_LANGUAGE: 'http://srv1022733.hstgr.cloud:8000/api/v1/legal-assistant/detect-language'
  },
  
  // Subscription & Premium Endpoints
  SUBSCRIPTION_ENDPOINTS: {
    STATUS: 'http://srv1022733.hstgr.cloud:8000/api/v1/subscriptions/status',
    PLANS: 'http://srv1022733.hstgr.cloud:8000/api/v1/subscriptions/plans',
    PREMIUM_STATUS: 'http://srv1022733.hstgr.cloud:8000/api/v1/premium/status',
    FEATURE_LIMITS: 'http://srv1022733.hstgr.cloud:8000/api/v1/premium/feature-limits'
  },
  
  // Enjaz Integration Endpoints
  ENJAZ_ENDPOINTS: {
    CONNECT: 'http://srv1022733.hstgr.cloud:8000/api/v1/enjaz/connect',
    SYNC_CASES: 'http://srv1022733.hstgr.cloud:8000/api/v1/enjaz/sync-cases',
    CASES: 'http://srv1022733.hstgr.cloud:8000/api/v1/enjaz/cases'
  },
  
  // Frontend URLs
  FRONTEND_URLS: {
    LOGIN: 'https://legatoo.westlinktowing.com/auth/login',
    SIGNUP: 'https://legatoo.westlinktowing.com/auth/signup',
    DASHBOARD: 'https://legatoo.westlinktowing.com/dashboard',
    EMAIL_VERIFICATION: 'https://legatoo.westlinktowing.com/email-verification.html',
    PASSWORD_RESET: 'https://legatoo.westlinktowing.com/password-reset.html'
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
