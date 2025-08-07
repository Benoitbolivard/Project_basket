// Shot Chart functionality for Basketball Analytics

class ShotChart {
    constructor() {
        this.canvas = document.getElementById('shot-chart-canvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.currentAnalysis = null;
        this.filteredShots = [];
        this.selectedShot = null;
        this.courtDimensions = {
            width: 600,
            height: 400
        };
        
        this.initializeEventListeners();
        this.loadAnalyses();
        this.drawCourt();
    }

    initializeEventListeners() {
        // Analysis selection
        const analysisSelect = document.getElementById('analysis-select');
        if (analysisSelect) {
            analysisSelect.addEventListener('change', (e) => this.loadAnalysis(e.target.value));
        }

        // Filter controls
        const filterControls = ['player-filter', 'shot-type-filter', 'zone-filter'];
        filterControls.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.applyFilters());
            }
        });

        // Canvas click handling
        if (this.canvas) {
            this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
            
            // Set canvas size
            this.canvas.width = this.courtDimensions.width;
            this.canvas.height = this.courtDimensions.height;
        }
    }

    async loadAnalyses() {
        try {
            const analysesData = await api.listAnalyses();
            this.populateAnalysisSelect(analysesData.analyses);
        } catch (error) {
            console.error('Failed to load analyses:', error);
            this.showError('Failed to load analysis list');
        }
    }

    populateAnalysisSelect(analyses) {
        const select = document.getElementById('analysis-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select an analysis</option>';
        
        if (analyses && analyses.length > 0) {
            analyses.forEach(analysis => {
                const option = document.createElement('option');
                option.value = analysis.analysis_id;
                option.textContent = `Analysis ${analysis.analysis_id.substring(0, 8)}... (${DataProcessor.formatDuration(analysis.duration)})`;
                select.appendChild(option);
            });
        }
    }

    async loadAnalysis(analysisId) {
        if (!analysisId) {
            this.currentAnalysis = null;
            this.filteredShots = [];
            this.clearCanvas();
            this.drawCourt();
            this.updateChartInfo('Select an analysis to view shot chart');
            this.updateZoneStats([]);
            return;
        }

        try {
            const results = await api.getAnalysisResults(analysisId);
            this.currentAnalysis = results;
            
            // Extract shots from results
            const shots = DataProcessor.extractShotAttempts(results);
            this.filteredShots = shots;
            
            // Update player filter
            this.updatePlayerFilter(results);
            
            // Draw chart
            this.drawShotChart();
            this.updateChartInfo(`Loaded ${shots.length} shots from analysis`);
            this.updateZoneStats(shots);
            
        } catch (error) {
            console.error('Failed to load analysis:', error);
            this.showError(`Failed to load analysis: ${error.message}`);
        }
    }

    updatePlayerFilter(results) {
        const playerFilter = document.getElementById('player-filter');
        if (!playerFilter) return;

        // Keep "All Players" option
        playerFilter.innerHTML = '<option value="all">All Players</option>';
        
        const playerStats = DataProcessor.getPlayerStats(results);
        Object.keys(playerStats).forEach(playerId => {
            const option = document.createElement('option');
            option.value = playerId;
            option.textContent = `Player ${playerId}`;
            playerFilter.appendChild(option);
        });
    }

    applyFilters() {
        if (!this.currentAnalysis) return;

        const allShots = DataProcessor.extractShotAttempts(this.currentAnalysis);
        
        const playerFilter = document.getElementById('player-filter')?.value || 'all';
        const shotTypeFilter = document.getElementById('shot-type-filter')?.value || 'all';
        const zoneFilter = document.getElementById('zone-filter')?.value || 'all';

        this.filteredShots = allShots.filter(shot => {
            // Player filter
            if (playerFilter !== 'all' && shot.shooter_id != playerFilter) {
                return false;
            }
            
            // Shot type filter
            if (shotTypeFilter === 'made' && !shot.made) {
                return false;
            }
            if (shotTypeFilter === 'missed' && shot.made) {
                return false;
            }
            
            // Zone filter
            if (zoneFilter !== 'all' && shot.zone !== zoneFilter) {
                return false;
            }
            
            return true;
        });

        this.drawShotChart();
        this.updateChartInfo(`Showing ${this.filteredShots.length} filtered shots`);
        this.updateZoneStats(this.filteredShots);
    }

    drawCourt() {
        if (!this.ctx) return;

        const { width, height } = this.courtDimensions;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Set court background
        this.ctx.fillStyle = '#d2691e'; // Basketball court color
        this.ctx.fillRect(0, 0, width, height);
        
        // Draw court lines
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 2;
        
        // Court outline
        this.ctx.strokeRect(50, 50, width - 100, height - 100);
        
        // Center line
        this.ctx.beginPath();
        this.ctx.moveTo(width / 2, 50);
        this.ctx.lineTo(width / 2, height - 50);
        this.ctx.stroke();
        
        // Center circle
        this.ctx.beginPath();
        this.ctx.arc(width / 2, height / 2, 40, 0, 2 * Math.PI);
        this.ctx.stroke();
        
        // Paint area (left basket)
        this.ctx.strokeRect(50, height / 2 - 60, 80, 120);
        
        // Paint area (right basket)
        this.ctx.strokeRect(width - 130, height / 2 - 60, 80, 120);
        
        // Three-point lines (simplified)
        this.ctx.beginPath();
        this.ctx.arc(130, height / 2, 100, -Math.PI / 2, Math.PI / 2);
        this.ctx.stroke();
        
        this.ctx.beginPath();
        this.ctx.arc(width - 130, height / 2, 100, Math.PI / 2, 3 * Math.PI / 2);
        this.ctx.stroke();
        
        // Baskets
        this.ctx.fillStyle = 'red';
        this.ctx.fillRect(45, height / 2 - 5, 10, 10);
        this.ctx.fillRect(width - 55, height / 2 - 5, 10, 10);
        
        // Zone labels
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';
        
        this.ctx.fillText('Paint', 90, height / 2);
        this.ctx.fillText('3PT', 180, height / 4);
        this.ctx.fillText('Mid Range', 250, height / 2);
        this.ctx.fillText('3PT', 420, height / 4);
        this.ctx.fillText('Paint', width - 90, height / 2);
    }

    drawShotChart() {
        this.drawCourt();
        
        if (!this.filteredShots || this.filteredShots.length === 0) {
            return;
        }

        // Draw shots
        this.filteredShots.forEach((shot, index) => {
            this.drawShot(shot, index);
        });
    }

    drawShot(shot, index) {
        if (!this.ctx) return;

        // Convert shot position to canvas coordinates
        const x = this.normalizeX(shot.x);
        const y = this.normalizeY(shot.y);
        
        // Shot appearance
        const radius = this.selectedShot === index ? 8 : 6;
        const color = this.selectedShot === index ? '#ffc107' : (shot.made ? '#28a745' : '#dc3545');
        
        this.ctx.fillStyle = color;
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.stroke();
        
        // Add make/miss indicator
        this.ctx.fillStyle = 'white';
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(shot.made ? '✓' : '✗', x, y);
    }

    normalizeX(x) {
        // Convert from video coordinates to canvas coordinates
        // Assuming video width is around 1920px, normalize to canvas width
        return Math.max(60, Math.min(this.courtDimensions.width - 60, (x / 1920) * this.courtDimensions.width));
    }

    normalizeY(y) {
        // Convert from video coordinates to canvas coordinates
        // Assuming video height is around 1080px, normalize to canvas height
        return Math.max(60, Math.min(this.courtDimensions.height - 60, (y / 1080) * this.courtDimensions.height));
    }

    handleCanvasClick(event) {
        if (!this.filteredShots || this.filteredShots.length === 0) return;

        const rect = this.canvas.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;

        // Find closest shot
        let closestShot = -1;
        let closestDistance = Infinity;

        this.filteredShots.forEach((shot, index) => {
            const shotX = this.normalizeX(shot.x);
            const shotY = this.normalizeY(shot.y);
            const distance = Math.sqrt((clickX - shotX) ** 2 + (clickY - shotY) ** 2);
            
            if (distance < 15 && distance < closestDistance) { // 15px click radius
                closestDistance = distance;
                closestShot = index;
            }
        });

        if (closestShot !== -1) {
            this.selectedShot = closestShot;
            this.drawShotChart();
            this.showShotDetails(this.filteredShots[closestShot]);
        }
    }

    showShotDetails(shot) {
        const detailsSection = document.getElementById('shot-details');
        const detailsContent = document.getElementById('shot-details-content');
        
        if (detailsSection) detailsSection.style.display = 'block';
        
        if (detailsContent) {
            detailsContent.innerHTML = `
                <div class="shot-detail-item">
                    <strong>Result:</strong> ${shot.made ? '✅ Made' : '❌ Missed'}
                </div>
                <div class="shot-detail-item">
                    <strong>Player:</strong> ${shot.shooter_id ? `Player ${shot.shooter_id}` : 'Unknown'}
                </div>
                <div class="shot-detail-item">
                    <strong>Zone:</strong> ${shot.zone || 'Unknown'}
                </div>
                <div class="shot-detail-item">
                    <strong>Position:</strong> (${Math.round(shot.x)}, ${Math.round(shot.y)})
                </div>
                <div class="shot-detail-item">
                    <strong>Time:</strong> ${DataProcessor.formatTimestamp(shot.timestamp)}
                </div>
                <div class="shot-detail-item">
                    <strong>Confidence:</strong> ${Math.round((shot.confidence || 0) * 100)}%
                </div>
                ${shot.shot_value ? `<div class="shot-detail-item"><strong>Points:</strong> ${shot.shot_value}</div>` : ''}
            `;
        }
    }

    updateZoneStats(shots) {
        const zoneStatsGrid = document.getElementById('zone-stats-grid');
        if (!zoneStatsGrid) return;

        if (!shots || shots.length === 0) {
            zoneStatsGrid.innerHTML = '<p class="empty-state">Select an analysis to view zone statistics</p>';
            return;
        }

        const zoneStats = DataProcessor.calculateZoneStats(shots);
        
        zoneStatsGrid.innerHTML = Object.keys(zoneStats).map(zone => {
            const stats = zoneStats[zone];
            return `
                <div class="zone-stat-card">
                    <h4>${this.formatZoneName(zone)}</h4>
                    <div class="zone-stat-item">
                        <span>Attempts:</span>
                        <span>${stats.attempts}</span>
                    </div>
                    <div class="zone-stat-item">
                        <span>Made:</span>
                        <span>${stats.made}</span>
                    </div>
                    <div class="zone-stat-item">
                        <span>Percentage:</span>
                        <span class="zone-percentage">${stats.percentage}%</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    formatZoneName(zone) {
        const zoneNames = {
            'paint': 'Paint',
            'three_point': 'Three Point',
            'mid_range': 'Mid Range',
            'unknown': 'Unknown Zone'
        };
        return zoneNames[zone] || zone;
    }

    updateChartInfo(message) {
        const chartInfo = document.getElementById('chart-info');
        if (chartInfo) {
            chartInfo.textContent = message;
        }
    }

    clearCanvas() {
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.courtDimensions.width, this.courtDimensions.height);
        }
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
}

// Modal functions
function closeShotModal() {
    const modal = document.getElementById('shot-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Initialize shot chart on page load
document.addEventListener('DOMContentLoaded', () => {
    window.shotChart = new ShotChart();
});

// Export ShotChart class
window.ShotChart = ShotChart;