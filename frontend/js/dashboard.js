// Dashboard functionality for Basketball Analytics

class Dashboard {
    constructor() {
        this.currentAnalysis = null;
        this.charts = {};
        this.refreshInterval = null;
        this.initializeEventListeners();
        this.checkAPIStatus();
        this.loadAnalyses();
        
        // Auto-refresh every 5 seconds for live stats
        this.startAutoRefresh();
    }

    initializeEventListeners() {
        // File upload handling
        const fileInput = document.getElementById('video-file');
        const uploadArea = document.getElementById('upload-area');

        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        if (uploadArea) {
            // Drag and drop functionality
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect({ target: { files: files } });
                }
            });

            uploadArea.addEventListener('click', () => {
                if (fileInput) fileInput.click();
            });
        }
    }

    async checkAPIStatus() {
        const statusElement = document.getElementById('api-status');
        const lastUpdateElement = document.getElementById('last-update');
        
        try {
            const health = await api.checkHealth();
            const apiInfo = await api.getAPIInfo();
            
            if (statusElement) {
                statusElement.textContent = health.status === 'healthy' ? '✅ Connected' : '❌ Error';
                statusElement.className = `status-value ${health.status === 'healthy' ? 'success' : 'error'}`;
            }
            
            if (lastUpdateElement) {
                lastUpdateElement.textContent = new Date().toLocaleTimeString();
            }
            
            console.log('API Status:', health, apiInfo);
        } catch (error) {
            console.error('API Status Check Failed:', error);
            if (statusElement) {
                statusElement.textContent = '❌ Offline';
                statusElement.className = 'status-value error';
            }
        }
    }

    async loadAnalyses() {
        try {
            const analysesData = await api.listAnalyses();
            this.displayAnalyses(analysesData.analyses);
        } catch (error) {
            console.error('Failed to load analyses:', error);
            this.showError('Failed to load analysis history');
        }
    }

    displayAnalyses(analyses) {
        const listElement = document.getElementById('analysis-list');
        if (!listElement) return;

        if (!analyses || analyses.length === 0) {
            listElement.innerHTML = '<p class="empty-state">No analyses available. Upload a video to get started!</p>';
            return;
        }

        listElement.innerHTML = analyses.map(analysis => `
            <div class="analysis-item">
                <div class="analysis-info">
                    <h4>Analysis ${analysis.analysis_id.substring(0, 8)}...</h4>
                    <p>Duration: ${DataProcessor.formatDuration(analysis.duration)} | 
                       Frames: ${analysis.total_frames} | 
                       Players: ${analysis.players_tracked}</p>
                </div>
                <div class="analysis-actions">
                    <button class="btn btn-small btn-primary" onclick="dashboard.loadAnalysis('${analysis.analysis_id}')">
                        📊 View
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="dashboard.downloadAnalysis('${analysis.analysis_id}')">
                        💾 Download
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="dashboard.deleteAnalysis('${analysis.analysis_id}')">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('video/')) {
            this.showError('Please select a valid video file');
            return;
        }

        // Show upload progress
        this.showUploadProgress();
        
        try {
            const response = await api.uploadAndAnalyzeVideo(file, {
                confidence_threshold: 0.25,
                visualize: true,
                save_frames: false,
                onProgress: (progress) => this.updateUploadProgress(progress)
            });

            if (response.success) {
                this.showSuccess('Video uploaded and analyzed successfully!');
                this.hideUploadProgress();
                this.loadAnalysis(response.analysis_id);
                this.loadAnalyses(); // Refresh the list
            } else {
                throw new Error(response.message || 'Analysis failed');
            }
        } catch (error) {
            console.error('Upload failed:', error);
            this.showError(`Upload failed: ${error.message}`);
            this.hideUploadProgress();
        }
    }

    showUploadProgress() {
        const uploadContent = document.querySelector('.upload-content');
        const uploadProgress = document.getElementById('upload-progress');
        
        if (uploadContent) uploadContent.style.display = 'none';
        if (uploadProgress) uploadProgress.style.display = 'block';
    }

    updateUploadProgress(progress) {
        const progressFill = document.getElementById('progress-fill');
        const uploadStatus = document.getElementById('upload-status');
        
        if (progressFill) progressFill.style.width = `${progress}%`;
        if (uploadStatus) uploadStatus.textContent = `Uploading... ${progress}%`;
    }

    hideUploadProgress() {
        const uploadContent = document.querySelector('.upload-content');
        const uploadProgress = document.getElementById('upload-progress');
        
        if (uploadContent) uploadContent.style.display = 'flex';
        if (uploadProgress) uploadProgress.style.display = 'none';
        
        // Reset file input
        const fileInput = document.getElementById('video-file');
        if (fileInput) fileInput.value = '';
    }

    async loadAnalysis(analysisId) {
        try {
            const results = await api.getAnalysisResults(analysisId);
            this.currentAnalysis = { id: analysisId, data: results };
            this.displayCurrentAnalysis(results);
            this.createLiveCharts(results);
        } catch (error) {
            console.error('Failed to load analysis:', error);
            this.showError(`Failed to load analysis: ${error.message}`);
        }
    }

    displayCurrentAnalysis(results) {
        const currentAnalysisSection = document.getElementById('current-analysis');
        if (currentAnalysisSection) {
            currentAnalysisSection.style.display = 'block';
        }

        const stats = DataProcessor.getSummaryStats(results);
        
        // Update stat cards
        this.updateElement('total-shots', stats.totalShots);
        this.updateElement('players-tracked', stats.playersTracked);
        this.updateElement('possession-changes', stats.possessionChanges);
        this.updateElement('game-duration', DataProcessor.formatDuration(stats.gameDuration));
    }

    createLiveCharts(results) {
        const liveStatsSection = document.getElementById('live-stats');
        if (liveStatsSection) {
            liveStatsSection.style.display = 'block';
        }

        // Create shot accuracy chart
        this.createShotAccuracyChart(results);
        
        // Create possession chart  
        this.createPossessionChart(results);
    }

    createShotAccuracyChart(results) {
        const ctx = document.getElementById('shot-accuracy-chart');
        if (!ctx) return;

        const playerStats = DataProcessor.getPlayerStats(results);
        const players = Object.keys(playerStats);
        
        if (players.length === 0) {
            ctx.innerHTML = '<p style="text-align: center; margin: 2rem; color: #666;">No player data available</p>';
            return;
        }

        // Create simple bar chart using canvas
        this.drawSimpleBarChart(ctx, {
            title: 'Player Shot Accuracy (%)',
            labels: players.map(id => `Player ${id}`),
            data: players.map(id => playerStats[id].field_goal_percentage || 0),
            color: '#ff6b35'
        });
    }

    createPossessionChart(results) {
        const ctx = document.getElementById('possession-chart');
        if (!ctx) return;

        const playerStats = DataProcessor.getPlayerStats(results);
        const players = Object.keys(playerStats);
        
        if (players.length === 0) {
            ctx.innerHTML = '<p style="text-align: center; margin: 2rem; color: #666;">No possession data available</p>';
            return;
        }

        // Create simple pie chart
        this.drawSimplePieChart(ctx, {
            title: 'Ball Possession Distribution',
            labels: players.map(id => `Player ${id}`),
            data: players.map(id => playerStats[id].possessions || 0)
        });
    }

    drawSimpleBarChart(container, config) {
        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 200;
        container.innerHTML = '';
        container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const { title, labels, data, color = '#ff6b35' } = config;
        
        // Chart dimensions
        const padding = 40;
        const chartWidth = canvas.width - (padding * 2);
        const chartHeight = canvas.height - (padding * 2);
        const barWidth = chartWidth / data.length;
        const maxValue = Math.max(...data, 1);
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw title
        ctx.fillStyle = '#333';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(title, canvas.width / 2, 20);
        
        // Draw bars
        data.forEach((value, index) => {
            const barHeight = (value / maxValue) * chartHeight;
            const x = padding + (index * barWidth) + (barWidth * 0.1);
            const y = padding + chartHeight - barHeight;
            const width = barWidth * 0.8;
            
            // Draw bar
            ctx.fillStyle = color;
            ctx.fillRect(x, y, width, barHeight);
            
            // Draw value on top
            ctx.fillStyle = '#333';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(Math.round(value), x + width/2, y - 5);
            
            // Draw label
            ctx.save();
            ctx.translate(x + width/2, canvas.height - 10);
            ctx.rotate(-Math.PI/4);
            ctx.textAlign = 'right';
            ctx.fillText(labels[index] || `Item ${index + 1}`, 0, 0);
            ctx.restore();
        });
    }

    drawSimplePieChart(container, config) {
        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 200;
        container.innerHTML = '';
        container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const { title, labels, data } = config;
        
        // Chart dimensions
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2 + 10;
        const radius = Math.min(canvas.width, canvas.height) / 3;
        const total = data.reduce((sum, value) => sum + value, 0);
        
        if (total === 0) {
            ctx.fillStyle = '#666';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', centerX, centerY);
            return;
        }
        
        // Colors for pie segments
        const colors = ['#ff6b35', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3'];
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw title
        ctx.fillStyle = '#333';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(title, centerX, 20);
        
        // Draw pie segments
        let currentAngle = -Math.PI / 2;
        data.forEach((value, index) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            
            // Draw slice
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = colors[index % colors.length];
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Draw label
            if (value > 0) {
                const labelAngle = currentAngle + sliceAngle / 2;
                const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
                const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
                
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(value.toString(), labelX, labelY);
            }
            
            currentAngle += sliceAngle;
        });
        
        // Draw legend
        const legendY = canvas.height - 40;
        let legendX = 20;
        labels.forEach((label, index) => {
            if (data[index] > 0) {
                // Color box
                ctx.fillStyle = colors[index % colors.length];
                ctx.fillRect(legendX, legendY, 12, 12);
                
                // Label text
                ctx.fillStyle = '#333';
                ctx.font = '10px Arial';
                ctx.textAlign = 'left';
                ctx.fillText(label, legendX + 16, legendY + 10);
                
                legendX += ctx.measureText(label).width + 30;
            }
        });
    }

    async downloadAnalysis(analysisId) {
        try {
            await api.downloadAnalysisJSON(analysisId);
            this.showSuccess('Analysis downloaded successfully!');
        } catch (error) {
            console.error('Download failed:', error);
            this.showError(`Download failed: ${error.message}`);
        }
    }

    async deleteAnalysis(analysisId) {
        if (!confirm('Are you sure you want to delete this analysis?')) {
            return;
        }

        try {
            await api.deleteAnalysis(analysisId);
            this.showSuccess('Analysis deleted successfully!');
            this.loadAnalyses(); // Refresh the list
            
            // Hide current analysis if it was the deleted one
            if (this.currentAnalysis && this.currentAnalysis.id === analysisId) {
                this.currentAnalysis = null;
                const currentAnalysisSection = document.getElementById('current-analysis');
                const liveStatsSection = document.getElementById('live-stats');
                if (currentAnalysisSection) currentAnalysisSection.style.display = 'none';
                if (liveStatsSection) liveStatsSection.style.display = 'none';
            }
        } catch (error) {
            console.error('Delete failed:', error);
            this.showError(`Delete failed: ${error.message}`);
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.checkAPIStatus();
        }, 5000); // Refresh every 5 seconds
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 2rem;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            transition: all 0.3s ease;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        `;

        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    // Cleanup method
    destroy() {
        this.stopAutoRefresh();
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
    }
}

// Refresh analyses function (called from HTML)
function refreshAnalyses() {
    if (window.dashboard) {
        window.dashboard.loadAnalyses();
    }
}

// Export Dashboard class
window.Dashboard = Dashboard;