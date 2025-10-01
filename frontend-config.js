// Frontend Configuration for Production
// This file provides the correct backend URL for authentication

const config = {
  // Production Backend URL
  BACKEND_URL: 'https://api.westlinktowing.com',
  API_BASE_URL: 'https://api.westlinktowing.com/api/v1',
  
  // Authentication Endpoints
  AUTH_ENDPOINTS: {
    LOGIN: 'https://api.westlinktowing.com/api/v1/auth/login',
    SIGNUP: 'https://api.westlinktowing.com/api/v1/auth/signup',
    REFRESH_TOKEN: 'https://api.westlinktowing.com/api/v1/auth/refresh-token',
    LOGOUT: 'https://api.westlinktowing.com/api/v1/auth/logout',
    FORGOT_PASSWORD: 'https://api.westlinktowing.com/api/v1/auth/forgot-password',
    CONFIRM_PASSWORD_RESET: 'https://api.westlinktowing.com/api/v1/auth/confirm-password-reset',
    VERIFY_EMAIL: 'https://api.westlinktowing.com/api/v1/auth/verify-email'
  },
  
  // User Management Endpoints
  USER_ENDPOINTS: {
    PROFILE: 'https://api.westlinktowing.com/api/v1/profiles/me',
    USERS: 'https://api.westlinktowing.com/api/v1/users',
    SEARCH_USERS: 'https://api.westlinktowing.com/api/v1/users/search'
  },
  
  // Contract Management Endpoints
  CONTRACT_ENDPOINTS: {
    CATEGORIES: 'https://api.westlinktowing.com/api/contracts/categories',
    TEMPLATES: 'https://api.westlinktowing.com/api/contracts/templates',
    USER_CONTRACTS: 'https://api.westlinktowing.com/api/v1/user-contracts',
    FAVORITES: 'https://api.westlinktowing.com/api/v1/favorites'
  },
  
  // Legal Assistant Endpoints (Updated for new implementation)
  LEGAL_ASSISTANT_ENDPOINTS: {
    UPLOAD: 'https://api.westlinktowing.com/api/v1/legal-assistant/documents/upload',
    SEARCH: 'https://api.westlinktowing.com/api/v1/legal-assistant/documents/search',
    DOCUMENTS: 'https://api.westlinktowing.com/api/v1/legal-assistant/documents',
    STATISTICS: 'https://api.westlinktowing.com/api/v1/legal-assistant/statistics'
  },
  
  // Subscription & Premium Endpoints
  SUBSCRIPTION_ENDPOINTS: {
    STATUS: 'https://api.westlinktowing.com/api/v1/subscriptions/status',
    PLANS: 'https://api.westlinktowing.com/api/v1/subscriptions/plans',
    PREMIUM_STATUS: 'https://api.westlinktowing.com/api/v1/premium/status',
    FEATURE_LIMITS: 'https://api.westlinktowing.com/api/v1/premium/feature-limits'
  },
  
  // Enjaz Integration Endpoints
  ENJAZ_ENDPOINTS: {
    CONNECT: 'https://api.westlinktowing.com/api/v1/enjaz/connect',
    SYNC_CASES: 'https://api.westlinktowing.com/api/v1/enjaz/sync-cases',
    CASES: 'https://api.westlinktowing.com/api/v1/enjaz/cases'
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
