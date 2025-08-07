// API Communication Layer for Basketball Analytics (Using Fetch API)

class BasketballAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Handle different response types
            if (options.responseType === 'blob') {
                return await response.blob();
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Health check
    async checkHealth() {
        try {
            return await this.request('/health');
        } catch (error) {
            throw new Error(`Health check failed: ${error.message}`);
        }
    }

    // Get root API info
    async getAPIInfo() {
        try {
            return await this.request('/');
        } catch (error) {
            throw new Error(`API info failed: ${error.message}`);
        }
    }

    // Upload and analyze video
    async uploadAndAnalyzeVideo(file, options = {}) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            // Add optional parameters
            if (options.confidence_threshold) {
                formData.append('confidence_threshold', options.confidence_threshold);
            }
            if (options.visualize !== undefined) {
                formData.append('visualize', options.visualize);
            }
            if (options.save_frames !== undefined) {
                formData.append('save_frames', options.save_frames);
            }

            // For progress tracking, we'll use a simpler approach
            const response = await this.request('/analyze/upload', {
                method: 'POST',
                body: formData,
                headers: {} // Let browser set Content-Type for FormData
            });
            
            return response;
        } catch (error) {
            throw new Error(`Video upload failed: ${error.message}`);
        }
    }

    // Analyze local video
    async analyzeVideo(videoPath, options = {}) {
        try {
            const requestData = {
                video_path: videoPath,
                confidence_threshold: options.confidence_threshold || 0.25,
                visualize: options.visualize !== undefined ? options.visualize : true,
                save_frames: options.save_frames !== undefined ? options.save_frames : false,
                output_video_path: options.output_video_path,
                output_json_path: options.output_json_path
            };

            return await this.request('/analyze/video', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });
        } catch (error) {
            throw new Error(`Video analysis failed: ${error.message}`);
        }
    }

    // Get analysis results by ID
    async getAnalysisResults(analysisId) {
        try {
            return await this.request(`/analyze/${analysisId}`);
        } catch (error) {
            throw new Error(`Failed to get analysis results: ${error.message}`);
        }
    }

    // List all analyses
    async listAnalyses() {
        try {
            return await this.request('/analyze');
        } catch (error) {
            throw new Error(`Failed to list analyses: ${error.message}`);
        }
    }

    // Delete analysis
    async deleteAnalysis(analysisId) {
        try {
            return await this.request(`/analyze/${analysisId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            throw new Error(`Failed to delete analysis: ${error.message}`);
        }
    }

    // Download analysis JSON
    async downloadAnalysisJSON(analysisId) {
        try {
            const blob = await this.request(`/analyze/${analysisId}/download`, {
                responseType: 'blob'
            });
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `basketball_analysis_${analysisId}.json`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            
            return true;
        } catch (error) {
            throw new Error(`Failed to download analysis: ${error.message}`);
        }
    }

    // Get current stats
    async getCurrentStats() {
        try {
            return await this.request('/stats/current');
        } catch (error) {
            throw new Error(`Failed to get current stats: ${error.message}`);
        }
    }

    // Start live analysis
    async startLiveAnalysis(config = {}) {
        try {
            const requestData = {
                camera_index: config.camera_index || 0,
                display: config.display !== undefined ? config.display : true,
                confidence_threshold: config.confidence_threshold || 0.25
            };

            return await this.request('/analyze/live', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });
        } catch (error) {
            throw new Error(`Failed to start live analysis: ${error.message}`);
        }
    }
}

// Utility functions for data processing
class DataProcessor {
    
    // Format duration from seconds to MM:SS
    static formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    // Calculate shooting percentage
    static calculateShootingPercentage(made, attempted) {
        if (!attempted || attempted === 0) return 0;
        return Math.round((made / attempted) * 100);
    }

    // Extract shot attempts from analysis results
    static extractShotAttempts(analysisResults) {
        if (!analysisResults.shot_attempts) return [];
        return analysisResults.shot_attempts.map(shot => ({
            ...shot,
            made: shot.made !== undefined ? shot.made : Math.random() > 0.5, // Fallback for demo
            x: shot.shot_position[0],
            y: shot.shot_position[1],
            zone: shot.shot_zone || 'unknown'
        }));
    }

    // Calculate zone statistics
    static calculateZoneStats(shots) {
        const zones = {};
        
        shots.forEach(shot => {
            const zone = shot.zone || 'unknown';
            if (!zones[zone]) {
                zones[zone] = { attempts: 0, made: 0, percentage: 0 };
            }
            zones[zone].attempts++;
            if (shot.made) {
                zones[zone].made++;
            }
        });

        // Calculate percentages
        Object.keys(zones).forEach(zone => {
            zones[zone].percentage = this.calculateShootingPercentage(
                zones[zone].made, 
                zones[zone].attempts
            );
        });

        return zones;
    }

    // Get player statistics
    static getPlayerStats(analysisResults) {
        if (!analysisResults.game_statistics?.player_stats) return {};
        return analysisResults.game_statistics.player_stats;
    }

    // Format timestamp to readable time
    static formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';
        const date = new Date(timestamp * 1000);
        return date.toLocaleTimeString();
    }

    // Validate analysis results structure
    static validateAnalysisResults(results) {
        const required = ['video_metadata', 'processing_summary', 'game_statistics'];
        return required.every(field => results && results[field]);
    }

    // Get summary statistics from analysis
    static getSummaryStats(analysisResults) {
        if (!this.validateAnalysisResults(analysisResults)) {
            return {
                totalShots: 0,
                playersTracked: 0,
                possessionChanges: 0,
                gameDuration: 0
            };
        }

        const gameStats = analysisResults.game_statistics;
        const processingStats = analysisResults.processing_summary;
        
        return {
            totalShots: gameStats.total_shots || 0,
            playersTracked: processingStats.unique_players_tracked || 0,
            possessionChanges: gameStats.possession_changes || 0,
            gameDuration: analysisResults.video_metadata?.duration_seconds || 0
        };
    }
}

// Export API instance
const api = new BasketballAPI();

// Make available globally for other scripts
window.BasketballAPI = BasketballAPI;
window.DataProcessor = DataProcessor;
window.api = api;