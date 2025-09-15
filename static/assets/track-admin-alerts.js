/* Track Admin Alerts - JavaScript for track admin import actions */

// Alert system using Django admin patterns
function showTrackAlert(message, type = 'info') {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertClass = type === 'error' ? 'alert-danger' : 
                     type === 'success' ? 'alert-success' : 
                     type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible">
            <button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>
            <i class="icon fa fa-${type === 'error' ? 'ban' : type === 'success' ? 'check' : type === 'warning' ? 'exclamation-triangle' : 'info'}"></i>
            ${message}
        </div>
    `;
    
    // Insert at the top of content
    const content = document.querySelector('#content');
    if (content) {
        content.insertAdjacentHTML('afterbegin', alertHtml);
    }
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Utility function to hide alerts
function hideTrackAlert() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());
}

// Generic fetch function for API calls
async function fetchTrackData(url, options = {}) {
    try {
        // Get CSRF token from various possible locations
        let csrfToken = null;
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            csrfToken = csrfInput.value;
        } else {
            // Try to get from meta tag
            const csrfMeta = document.querySelector('meta[name=csrf-token]');
            if (csrfMeta) {
                csrfToken = csrfMeta.getAttribute('content');
            }
        }
        
        console.log('CSRF token found:', csrfToken ? 'Yes' : 'No');
        
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                ...options.headers
            },
            ...options
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Track metadata fetch function
function fetchTrackMetadata(trackId, button) {
    console.log('fetchTrackMetadata called with trackId:', trackId);
    const originalText = button.value;
    button.value = 'Fetching...';
    button.disabled = true;
    
    hideTrackAlert();
    
    const url = `/admin/soundcharts/track/${trackId}/fetch-metadata/`;
    console.log('Making request to:', url);
    
    fetchTrackData(url, {
        method: 'POST'
    })
    .then(data => {
        console.log('Metadata fetch response:', data);
        if (data.success) {
            showTrackAlert(data.message, 'success');
            // Reload the page to show updated data
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showTrackAlert(data.error || 'Failed to fetch metadata', 'error');
            button.value = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTrackAlert('Error fetching metadata: ' + error.message, 'error');
        button.value = originalText;
        button.disabled = false;
    });
}

// Track audience fetch function
function fetchTrackAudience(trackId, button) {
    console.log('fetchTrackAudience called with trackId:', trackId);
    const originalText = button.value;
    button.value = 'Fetching...';
    button.disabled = true;
    
    // Get platform and force refresh values
    const platform = document.getElementById('platform_select')?.value || 'spotify';
    const forceRefresh = document.querySelector('input[name="force_refresh"]')?.checked || false;
    
    console.log('Platform:', platform, 'Force refresh:', forceRefresh);
    
    hideTrackAlert();
    
    const url = `/admin/soundcharts/track/${trackId}/fetch-audience/`;
    console.log('Making request to:', url);
    
    fetchTrackData(url, {
        method: 'POST',
        body: JSON.stringify({
            platform: platform,
            force_refresh: forceRefresh
        })
    })
    .then(data => {
        console.log('Audience fetch response:', data);
        if (data.success) {
            showTrackAlert(data.message, 'success');
            // Reload the page to show updated data
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showTrackAlert(data.error || 'Failed to fetch audience data', 'error');
            button.value = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTrackAlert('Error fetching audience data: ' + error.message, 'error');
        button.value = originalText;
        button.disabled = false;
    });
}

// Bulk metadata fetch function for changelist
function fetchBulkMetadata() {
    const checkboxes = document.querySelectorAll('input[name="_selected_action"]:checked');
    if (checkboxes.length === 0) {
        showTrackAlert('Please select at least one track to fetch metadata for.', 'warning');
        return;
    }
    
    const trackIds = Array.from(checkboxes).map(cb => cb.value);
    
    hideTrackAlert();
    showTrackAlert(`Starting metadata fetch for ${trackIds.length} tracks...`, 'info');
    
    fetchTrackData('/admin/soundcharts/track/bulk-fetch-metadata/', {
        method: 'POST',
        body: JSON.stringify({
            track_ids: trackIds
        })
    })
    .then(data => {
        if (data.success) {
            showTrackAlert(data.message, 'success');
            // Reload the page to show updated data
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showTrackAlert(data.error || 'Failed to start bulk metadata fetch', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTrackAlert('Error starting bulk metadata fetch: ' + error.message, 'error');
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Track admin alerts script loaded');
    
    // Add event listeners for the import buttons directly
    const fetchMetadataBtn = document.querySelector('input[name="_fetch_metadata"]');
    console.log('Metadata button found:', fetchMetadataBtn);
    if (fetchMetadataBtn) {
        fetchMetadataBtn.addEventListener('click', function(e) {
            console.log('Metadata button clicked');
            e.preventDefault();
            const trackId = window.location.pathname.match(/\/track\/(\d+)\//)?.[1];
            console.log('Track ID extracted:', trackId);
            if (trackId) {
                fetchTrackMetadata(trackId, this);
            } else {
                showTrackAlert('Could not determine track ID from URL', 'error');
            }
        });
    }
    
    const fetchAudienceBtn = document.querySelector('input[name="_fetch_audience"]');
    console.log('Audience button found:', fetchAudienceBtn);
    if (fetchAudienceBtn) {
        fetchAudienceBtn.addEventListener('click', function(e) {
            console.log('Audience button clicked');
            e.preventDefault();
            const trackId = window.location.pathname.match(/\/track\/(\d+)\//)?.[1];
            console.log('Track ID extracted:', trackId);
            if (trackId) {
                fetchTrackAudience(trackId, this);
            } else {
                showTrackAlert('Could not determine track ID from URL', 'error');
            }
        });
    }
    
    // Add event listener for bulk metadata button
    const bulkMetadataBtn = document.querySelector('a[onclick*="createBulkMetadataTask"]');
    console.log('Bulk metadata button found:', bulkMetadataBtn);
    if (bulkMetadataBtn) {
        bulkMetadataBtn.onclick = function(e) {
            e.preventDefault();
            if (confirm('This will create a background task to fetch metadata for all selected tracks. Continue?')) {
                fetchBulkMetadata();
            }
        };
    }
});
