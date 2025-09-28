/**
 * Centralized URL configuration for frontend JavaScript.
 * 
 * This file provides a single source of truth for all URLs used in
 * the frontend HTML files, ensuring consistency and easy maintenance.
 */

class URLConfig {
    constructor() {
        // Environment detection
        this.environment = this.detectEnvironment();
        
        // Base URLs - can be overridden by environment variables or build process
        this.frontendUrl = this.getEnvVar('FRONTEND_URL') || this.getDefaultFrontendUrl();
        this.backendUrl = this.getEnvVar('BACKEND_URL') || this.getDefaultBackendUrl();
        this.apiBaseUrl = `${this.backendUrl}/api/v1`;
    }

    detectEnvironment() {
        // Detect environment based on hostname
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        } else if (hostname.includes('legatoo.westlinktowing.com')) {
            return 'production';
        }
        return 'development';
    }

    getEnvVar(name) {
        // Try to get from meta tag or global variable
        const metaTag = document.querySelector(`meta[name="${name}"]`);
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Check if defined globally
        if (window[name]) {
            return window[name];
        }
        
        return null;
    }

    getDefaultFrontendUrl() {
        if (this.environment === 'production') {
            return 'https://legatoo.westlinktowing.com';
        }
        return 'http://localhost:3000';
    }

    getDefaultBackendUrl() {
        if (this.environment === 'production') {
            return 'https://api.legatoo.westlinktowing.com';
        }
        return 'http://127.0.0.1:8000';
    }

    get authUrls() {
        return {
            login: `${this.frontendUrl}/auth/login`,
            signup: `${this.frontendUrl}/auth/signup`,
            forgotPassword: `${this.frontendUrl}/auth/forgot-password`,
            emailVerification: `${this.frontendUrl}/email-verification.html`,
            passwordReset: `${this.frontendUrl}/password-reset.html`,
            dashboard: `${this.frontendUrl}/dashboard`,
        };
    }

    get apiUrls() {
        return {
            authBase: `${this.apiBaseUrl}/auth`,
            login: `${this.apiBaseUrl}/auth/login`,
            signup: `${this.apiBaseUrl}/auth/signup`,
            verifyEmail: `${this.apiBaseUrl}/auth/verify-email`,
            forgotPassword: `${this.apiBaseUrl}/auth/forgot-password`,
            confirmPasswordReset: `${this.apiBaseUrl}/auth/confirm-password-reset`,
            refreshToken: `${this.apiBaseUrl}/auth/refresh-token`,
            logout: `${this.apiBaseUrl}/auth/logout`,
            profile: `${this.apiBaseUrl}/profiles/me`,
            subscriptions: `${this.apiBaseUrl}/subscriptions/status`,
            plans: `${this.apiBaseUrl}/subscriptions/plans`,
            premium: `${this.apiBaseUrl}/premium/status`,
            features: `${this.apiBaseUrl}/premium/feature-limits`,
        };
    }

    getVerificationUrl(token) {
        return `${this.authUrls.emailVerification}?token=${token}`;
    }

    getPasswordResetUrl(token) {
        return `${this.authUrls.passwordReset}?token=${token}`;
    }

    getApiUrl(endpoint) {
        return this.apiUrls[endpoint] || `${this.apiBaseUrl}/${endpoint}`;
    }

    getFrontendUrl(path = '') {
        return path ? `${this.frontendUrl}/${path.replace(/^\//, '')}` : this.frontendUrl;
    }

    toObject() {
        return {
            environment: this.environment,
            frontendUrl: this.frontendUrl,
            backendUrl: this.backendUrl,
            apiBaseUrl: this.apiBaseUrl,
            authUrls: this.authUrls,
            apiUrls: this.apiUrls,
        };
    }
}

// Global instance
window.urlConfig = new URLConfig();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = URLConfig;
}
