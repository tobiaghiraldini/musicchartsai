import ApexCharts from 'apexcharts';

// Audience Charts Manager - handles audience analytics dashboard
class AudienceChartsManager {
    constructor() {
        this.tracks = [];
        this.charts = new Map();
        this.currentFilters = {
            dateRange: 30,
            platform: 'all'
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTracks();
    }

    bindEvents() {
        // Date range filter
        document.getElementById('date-range')?.addEventListener('change', (e) => {
            this.currentFilters.dateRange = parseInt(e.target.value);
            this.updateAllCharts();
        });

        // Platform filter
        document.getElementById('platform-filter')?.addEventListener('change', (e) => {
            this.currentFilters.platform = e.target.value;
            this.filterTracks();
        });

        // Refresh data button
        document.getElementById('refresh-data')?.addEventListener('click', () => {
            this.refreshAllData();
        });

        // Dark mode toggle listener
        document.addEventListener('dark-mode', () => {
            this.updateAllCharts();
        });
    }

    async loadTracks() {
        this.showLoading();
        this.hideError();
        
        try {
            // Fetch tracks with audience data
            const response = await fetch('/soundcharts/api/tracks-with-audience/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            this.tracks = data.tracks || [];
            
            if (this.tracks.length === 0) {
                this.showEmptyState();
            } else {
                this.renderTracks();
            }
            
        } catch (error) {
            console.error('Error loading tracks:', error);
            this.showError('Failed to load tracks data');
        } finally {
            this.hideLoading();
        }
    }

    async refreshAllData() {
        this.showLoading();
        this.hideError();
        
        try {
            // Refresh data for all tracks
            const refreshPromises = this.tracks.map(track => 
                this.refreshTrackData(track.uuid)
            );
            
            await Promise.all(refreshPromises);
            
            // Reload tracks after refresh
            await this.loadTracks();
            
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh data');
        } finally {
            this.hideLoading();
        }
    }

    async refreshTrackData(trackUuid) {
        try {
            // Get platforms for this track
            const platforms = await this.getTrackPlatforms(trackUuid);
            
            // Get CSRF token
            const csrfToken = this.getCSRFToken();
            console.log('CSRF Token length:', csrfToken.length);
            console.log('CSRF Token preview:', csrfToken.substring(0, 10) + '...');
            
            if (!csrfToken) {
                throw new Error('CSRF token not available');
            }
            
            // Refresh data for each platform
            const refreshPromises = platforms.map(platform => {
                const url = `/soundcharts/audience/refresh/${trackUuid}/${platform.slug}/`;
                console.log('Refreshing data for:', url);
                
                return fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                }).then(response => {
                    console.log(`Response for ${platform.slug}:`, response.status, response.statusText);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response;
                });
            });
            
            await Promise.all(refreshPromises);
            console.log('Successfully refreshed data for track:', trackUuid);
            
        } catch (error) {
            console.error(`Error refreshing data for track ${trackUuid}:`, error);
        }
    }

    async getTrackPlatforms(trackUuid) {
        try {
            const response = await fetch(`/soundcharts/audience/chart/${trackUuid}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.platforms || [];
            
        } catch (error) {
            console.error(`Error getting platforms for track ${trackUuid}:`, error);
            return [];
        }
    }

    renderTracks() {
        const container = document.getElementById('tracks-container');
        container.innerHTML = '';
        
        const filteredTracks = this.filterTracks();
        
        filteredTracks.forEach(track => {
            const trackCard = this.createTrackCard(track);
            container.appendChild(trackCard);
        });
        
        this.hideEmptyState();
    }

    filterTracks() {
        if (this.currentFilters.platform === 'all') {
            return this.tracks;
        }
        
        return this.tracks.filter(track => 
            track.platforms.some(platform => platform.slug === this.currentFilters.platform)
        );
    }

    createTrackCard(track) {
        const template = document.getElementById('track-card-template');
        const card = template.content.cloneNode(true);
        
        // Set track information
        card.querySelector('#track-name').textContent = track.name;
        card.querySelector('#track-artist').textContent = track.credit_name || 'Unknown Artist';
        card.querySelector('#track-uuid').textContent = `UUID: ${track.uuid}`;
        
        // Set track image
        const trackImage = card.querySelector('#track-image');
        if (track.image_url) {
            trackImage.src = track.image_url;
            trackImage.alt = track.name;
        } else {
            trackImage.src = '/static/dist/images/default-track.png';
            trackImage.alt = 'Default track image';
        }
        
        // Set track status
        const status = card.querySelector('#track-status');
        if (track.audience_fetched_at) {
            const lastUpdate = new Date(track.audience_fetched_at);
            const daysSinceUpdate = Math.floor((new Date() - lastUpdate) / (1000 * 60 * 60 * 24));
            
            if (daysSinceUpdate <= 1) {
                status.textContent = 'Active';
                status.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            } else if (daysSinceUpdate <= 7) {
                status.textContent = 'Stale';
                status.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
            } else {
                status.textContent = 'Outdated';
                status.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            }
        } else {
            status.textContent = 'No Data';
            status.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
        }
        
        // Create platform charts
        const platformChartsContainer = card.querySelector('#platform-charts');
        track.platforms.forEach(platform => {
            const platformChart = this.createPlatformChart(track, platform);
            platformChartsContainer.appendChild(platformChart);
        });
        
        return card;
    }

    createPlatformChart(track, platform) {
        const template = document.getElementById('platform-chart-template');
        const chart = template.content.cloneNode(true);
        
        // Set platform information
        chart.querySelector('#platform-name').textContent = platform.name;
        chart.querySelector('#platform-metric').textContent = platform.metric_name || 'Listeners';
        
        // Set chart container ID
        const chartContainer = chart.querySelector('#chart-container');
        const chartId = `chart-${track.uuid}-${platform.slug}`;
        chartContainer.id = chartId;
        
        // Set data points info
        chart.querySelector('#data-points').textContent = `${this.currentFilters.dateRange} days`;
        chart.querySelector('#date-range').textContent = `Last ${this.currentFilters.dateRange} days`;
        
        // Load and render chart data with a small delay to ensure DOM is ready
        setTimeout(() => {
            this.loadChartData(track.uuid, platform.slug, chartId, platform);
        }, 100);
        
        return chart;
    }

    async loadChartData(trackUuid, platformSlug, chartId, platform) {
        try {
            const url = `/soundcharts/audience/chart/${trackUuid}/${platformSlug}/?limit=${this.currentFilters.dateRange}`;

            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            
            if (data.success && data.chart_data) {
                this.renderChart(chartId, data.chart_data, platform);
                
                // Update latest value
                const latestValue = data.chart_data.datasets[0]?.data?.slice(-1)[0];
                if (latestValue) {
                    const latestValueElement = document.querySelector(`#${chartId}`).closest('.platform-chart').querySelector('#latest-value');
                    latestValueElement.textContent = this.formatNumber(latestValue);
                }
            } else {

                this.renderEmptyChart(chartId, platform);
            }
            
        } catch (error) {
            console.error(`Error loading chart data for ${trackUuid} on ${platformSlug}:`, error);
            this.renderEmptyChart(chartId, platform);
        }
    }

    renderChart(chartId, chartData, platform) {
        const chartColors = this.getChartColors();
        const platformColor = this.getPlatformColor(platform.slug);
        
        const options = {
            chart: {
                type: 'area',
                height: 140,
                fontFamily: 'Inter, sans-serif',
                foreColor: chartColors.labelColor,
                toolbar: {
                    show: false
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: {
                        enabled: true,
                        delay: 150
                    },
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350
                    }
                }
            },
            series: [{
                name: platform.metric_name || 'Listeners',
                data: chartData.datasets[0].data
            }],
            colors: [platformColor],
            stroke: {
                curve: 'smooth',
                width: 3,
                lineCap: 'round'
            },
            fill: {
                type: 'gradient',
                gradient: {
                    enabled: true,
                    opacityFrom: chartColors.opacityFrom,
                    opacityTo: chartColors.opacityTo,
                    stops: [0, 100]
                }
            },
            markers: {
                size: 4,
                strokeColors: '#ffffff',
                strokeWidth: 2,
                hover: {
                    size: 6,
                    sizeOffset: 2
                }
            },
            xaxis: {
                categories: chartData.labels,
                labels: {
                    show: false
                },
                axisBorder: {
                    show: false
                },
                axisTicks: {
                    show: false
                }
            },
            yaxis: {
                labels: {
                    show: false
                }
            },
            grid: {
                show: false
            },
            tooltip: {
                enabled: true,
                style: {
                    fontSize: '12px',
                    fontFamily: 'Inter, sans-serif'
                },
                y: {
                    formatter: (value) => this.formatNumber(value)
                }
            },
            dataLabels: {
                enabled: false
            },
            legend: {
                show: false
            }
        };

        // Destroy existing chart if it exists
        if (this.charts.has(chartId)) {
            this.charts.get(chartId).destroy();
        }

        // Create new chart
        const chart = new ApexCharts(document.getElementById(chartId), options);
        chart.render();
        this.charts.set(chartId, chart);
    }

    renderEmptyChart(chartId, platform) {
        const chartColors = this.getChartColors();
        
        const options = {
            chart: {
                type: 'area',
                height: 140,
                fontFamily: 'Inter, sans-serif',
                foreColor: chartColors.labelColor,
                toolbar: {
                    show: false
                }
            },
            series: [{
                name: platform.metric_name || 'Listeners',
                data: []
            }],
            colors: [chartColors.labelColor],
            stroke: {
                curve: 'smooth',
                width: 2
            },
            fill: {
                type: 'gradient',
                gradient: {
                    enabled: true,
                    opacityFrom: 0.1,
                    opacityTo: 0.05,
                    stops: [0, 100]
                }
            },
            xaxis: {
                labels: {
                    show: false
                },
                axisBorder: {
                    show: false
                },
                axisTicks: {
                    show: false
                }
            },
            yaxis: {
                labels: {
                    show: false
                }
            },
            grid: {
                show: false
            },
            tooltip: {
                enabled: false
            },
            dataLabels: {
                enabled: false
            },
            legend: {
                show: false
            },
            annotations: {
                yaxis: [{
                    y: 50,
                    borderColor: chartColors.labelColor,
                    label: {
                        text: 'No data available',
                        style: {
                            color: chartColors.labelColor,
                            fontSize: '12px'
                        }
                    }
                }]
            }
        };

        // Destroy existing chart if it exists
        if (this.charts.has(chartId)) {
            this.charts.get(chartId).destroy();
        }

        // Create new chart
        const chart = new ApexCharts(document.getElementById(chartId), options);
        chart.render();
        this.charts.set(chartId, chart);
    }

    updateAllCharts() {
        this.charts.forEach((chart, chartId) => {
            // Extract track UUID and platform from chart ID
            const parts = chartId.split('-');
            if (parts.length >= 3) {
                const trackUuid = parts[1];
                const platformSlug = parts[2];
                
                // Find the platform info
                const track = this.tracks.find(t => t.uuid === trackUuid);
                if (track) {
                    const platform = track.platforms.find(p => p.slug === platformSlug);
                    if (platform) {
                        this.loadChartData(trackUuid, platformSlug, chartId, platform);
                    }
                }
            }
        });
    }

    getChartColors() {
        if (document.documentElement.classList.contains('dark')) {
            return {
                primary: '#1A56DB',
                primaryLight: '#3B82F6',
                secondary: '#10B981',
                secondaryLight: '#059669',
                labelColor: '#9CA3AF',
                borderColor: '#374151',
                opacityFrom: 0,
                opacityTo: 0.15
            };
        } else {
            return {
                primary: '#1A56DB',
                primaryLight: '#3B82F6',
                secondary: '#10B981',
                secondaryLight: '#34D399',
                labelColor: '#6B7280',
                borderColor: '#F3F4F6',
                opacityFrom: 0.45,
                opacityTo: 0
            };
        }
    }

    getPlatformColor(platformSlug) {
        const colors = {
            'spotify': '#1DB954',
            'apple_music': '#FA233B',
            'youtube': '#FF0000',
            'tiktok': '#000000',
            'soundcloud': '#FF5500',
            'deezer': '#00C7F2',
            'amazon_music': '#00A8E1',
            'pandora': '#224099'
        };
        
        return colors[platformSlug] || '#1A56DB';
    }

    formatNumber(value) {
        if (value >= 1_000_000_000) {
            return (value / 1_000_000_000).toFixed(1) + 'B';
        } else if (value >= 1_000_000) {
            return (value / 1_000_000).toFixed(1) + 'M';
        } else if (value >= 1_000) {
            return (value / 1_000).toFixed(1) + 'K';
        } else {
            return value.toLocaleString();
        }
    }

    getCSRFToken() {
        // Try to get CSRF token from form input first
        const formToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (formToken && formToken.length > 0) {
            return formToken;
        }
        
        // Try to get CSRF token from meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (metaToken && metaToken.length > 0) {
            return metaToken;
        }
        
        // If no token found, log error and return empty string
        console.error('CSRF token not found. Make sure the template includes a CSRF token.');
        return '';
    }

    showLoading() {
        document.getElementById('loading-state').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-state').classList.add('hidden');
    }

    showError(message) {
        const errorState = document.getElementById('error-state');
        const errorMessage = document.getElementById('error-message');
        errorMessage.textContent = message;
        errorState.classList.remove('hidden');
    }

    hideError() {
        document.getElementById('error-state').classList.add('hidden');
    }

    showEmptyState() {
        document.getElementById('empty-state').classList.remove('hidden');
    }

    hideEmptyState() {
        document.getElementById('empty-state').classList.add('hidden');
    }
}

// Initialize the audience charts manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AudienceChartsManager();
});
