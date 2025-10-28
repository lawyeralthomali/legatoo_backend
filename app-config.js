// Dynamic Configuration for HTML Pages
// This script automatically detects the environment and sets the correct API base URL

(function() {
    'use strict';
    
    // Configuration object
    const config = {
        // Detect environment based on current domain
        getEnvironment: function() {
            const hostname = window.location.hostname;
            
            if (hostname.includes('fastestfranchise.net') || hostname.includes('westlinktowing.com') || hostname.includes('srv1022733.hstgr.cloud')) {
                return 'production';
            } else if (hostname.includes('localhost') || hostname.includes('127.0.0.1')) {
                return 'development';
            } else {
                return 'production'; // Default to production for unknown domains
            }
        },
        
        // Get API base URL based on environment
        getApiBaseUrl: function() {
            const environment = this.getEnvironment();
            
            switch (environment) {
                case 'production':
                    return 'https://api.fastestfranchise.net/api/v1/auth';
                case 'development':
                    return 'http://127.0.0.1:8000/api/v1/auth';
                default:
                    return 'https://api.fastestfranchise.net/api/v1/auth';
            }
        },
        
        // Get frontend URL based on environment
        getFrontendUrl: function() {
            const environment = this.getEnvironment();
            
            switch (environment) {
                case 'production':
                    return 'https://legatoo.fastestfranchise.net';
                case 'development':
                    return 'http://localhost:3000';
                default:
                    return 'https://legatoo.fastestfranchise.net';
            }
        },
        
        // Get all configuration
        getAll: function() {
            return {
                environment: this.getEnvironment(),
                apiBaseUrl: this.getApiBaseUrl(),
                frontendUrl: this.getFrontendUrl(),
                authEndpoints: {
                    login: this.getFrontendUrl() + '/auth/login/',
                    signup: this.getFrontendUrl() + '/auth/signup',
                    forgotPassword: this.getFrontendUrl() + '/auth/forgot-password'
                }
            };
        }
    };
    
    // Make config available globally
    window.APP_CONFIG = config;
    
    // Log configuration for debugging
    console.log('App Configuration:', config.getAll());
})();
