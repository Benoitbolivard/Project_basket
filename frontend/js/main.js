// Main application initialization

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard if on dashboard page
    if (document.getElementById('upload-area')) {
        window.dashboard = new Dashboard();
        console.log('Dashboard initialized');
    }
    
    // Add global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
    });
    
    // Add unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
    });
    
    console.log('Basketball Analytics Frontend initialized');
});

// Global utility functions
window.BasketballUtils = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Validate video file
    isValidVideoFile: function(file) {
        const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/webm'];
        return validTypes.includes(file.type);
    },
    
    // Get video duration (returns promise)
    getVideoDuration: function(file) {
        return new Promise((resolve, reject) => {
            const video = document.createElement('video');
            video.preload = 'metadata';
            
            video.onloadedmetadata = function() {
                window.URL.revokeObjectURL(video.src);
                resolve(video.duration);
            };
            
            video.onerror = function() {
                window.URL.revokeObjectURL(video.src);
                reject('Unable to get video duration');
            };
            
            video.src = URL.createObjectURL(file);
        });
    },
    
    // Debounce function
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }
};

// Add some helpful console messages for developers
console.log(`
🏀 Basketball Analytics Frontend
================================
Available global objects:
- api: BasketballAPI instance
- dashboard: Dashboard instance (on dashboard page)
- shotChart: ShotChart instance (on shot chart page)
- DataProcessor: Data processing utilities
- BasketballUtils: General utilities

API Base URL: ${window.api ? window.api.baseURL : 'Not initialized'}
`);

// Service worker registration (if we had one)
if ('serviceWorker' in navigator) {
    // Placeholder for future PWA features
    console.log('Service worker support detected');
}