/* Admin Import Views - Unified JavaScript */

// Global variables
let currentData = null;
let currentCharts = null;

// Alert system using Django admin patterns
function showAlert(message, type = 'info') {
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

// Loading state management
function showLoading(show = true) {
    console.log('showLoading called with:', show);
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = show ? 'block' : 'none';
        console.log('Loading element display set to:', loading.style.display);
    } else {
        console.error('Loading element with id="loading" not found');
    }
}

// Generic fetch function for API calls
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Chart Import Functions
function fetchCharts() {
    console.log('fetchCharts() called');
    const form = document.getElementById('fetchForm');
    if (!form) {
        console.error('Form with id="fetchForm" not found');
        return;
    }
    
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    console.log('Form data:', Object.fromEntries(formData));
    console.log('Params:', params.toString());
    
    showLoading(true);
    hideAlert();
    
    // Use the form action URL
    const fetchUrl = form.action;
    console.log('Fetch URL:', fetchUrl);
    
    // For GET requests, we don't need to send the CSRF token in the body
    fetch(`${fetchUrl}?${params.toString()}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('API response:', data);
        showLoading(false);
        if (data.success === true) {
            currentCharts = data.charts;
            displayCharts(data.charts);
        } else {
            showAlert('Error fetching charts: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showLoading(false);
        showAlert('Error fetching charts. Please try again.', 'error');
    });
}

function displayCharts(charts) {
    const container = document.getElementById('chartsContainer');
    const table = document.getElementById('chartsTable');
    const tbody = table.querySelector('tbody');
    
    if (!charts || !Array.isArray(charts)) {
        showAlert('Invalid charts data received', 'error');
        return;
    }
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add chart rows
    charts.forEach((chart, index) => {
        const row = document.createElement('tr');
        const isExisting = chart.already_exists;
        const buttonText = isExisting ? 'Already Added' : 'Add';
        const buttonClass = isExisting ? 'btn-add disabled' : 'btn-add';
        const buttonOnclick = isExisting ? '' : `onclick="addChart('${chart.slug}', this)"`;
        
        row.innerHTML = `
            <td>
                <div class="chart-name">${chart.name}</div>
                <div class="chart-meta">Type: ${chart.type} | Frequency: ${chart.frequency}</div>
            </td>
            <td>${chart.slug}</td>
            <td>${chart.country_code}</td>
            <td>
                <div class="action-buttons">
                    <button type="button" class="${buttonClass}" ${buttonOnclick} ${isExisting ? 'disabled' : ''}>
                        ${buttonText}
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Show charts section
    container.style.display = 'block';
    document.getElementById('fetchSection').style.display = 'none';
    
    // Add "Add All" button (only for non-existing charts)
    const newCharts = charts.filter(chart => !chart.already_exists);
    if (newCharts.length > 0) {
        // Remove any existing "Add All" button first
        const existingAddAllBtn = container.querySelector('.btn-add-all');
        if (existingAddAllBtn) {
            existingAddAllBtn.remove();
        }
        
        const addAllBtn = document.createElement('button');
        addAllBtn.type = 'button';
        addAllBtn.className = 'btn-add-all';
        addAllBtn.textContent = `Add All ${newCharts.length} New Charts`;
        addAllBtn.onclick = () => addAllCharts(newCharts);
        
        // Insert the button at the beginning of the container
        container.insertBefore(addAllBtn, container.firstChild);
    }
    
    // Show success message
    const existingCount = charts.filter(chart => chart.already_exists).length;
    const newCount = newCharts.length;
    let message = `Successfully fetched ${charts.length} charts`;
    if (existingCount > 0 && newCount > 0) {
        message += ` (${existingCount} already exist, ${newCount} new)`;
    } else if (existingCount > 0) {
        message += ` (all already exist)`;
    } else {
        message += ` (all new)`;
    }
    showAlert(message, 'success');
}

function addChart(slug, button) {
    button.disabled = true;
    button.textContent = 'Adding...';
    
    // Construct the add URL based on current path
    const addUrl = window.location.pathname.replace('import/', 'add/');
    
    fetchData(addUrl, {
        method: 'POST',
        body: JSON.stringify({ slug: slug })
    })
    .then(data => {
        if (data.success) {
            button.textContent = 'Added';
            button.style.background = '#28a745';
            button.classList.add('disabled');
        } else {
            button.textContent = 'Error';
            button.style.background = '#dc3545';
            showAlert(data.error || 'Error adding chart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.textContent = 'Error';
        button.style.background = '#dc3545';
        showAlert('Error adding chart', 'error');
    });
}

function addAllCharts(charts) {
    const addButtons = document.querySelectorAll('.btn-add');
    addButtons.forEach(button => {
        if (!button.disabled) {
            button.click();
        }
    });
}

// Rankings Import Functions
function fetchRankings() {
    const rankingDate = document.getElementById('ranking_date');
    const dateValue = rankingDate ? rankingDate.value : '';
    
    showLoading(true);
    
    const data = {};
    if (dateValue) {
        data.ranking_date = dateValue;
    }
    
    // Construct the fetch rankings URL based on current path
    const fetchUrl = window.location.pathname.replace('import-rankings/', 'api/fetch-rankings/');
    
    fetchData(fetchUrl, {
        method: 'POST',
        body: JSON.stringify(data)
    })
    .then(data => {
        showLoading(false);
        if (data.error) {
            showAlert(data.error, 'error');
        } else {
            currentData = data.data;
            displayResults();
        }
    })
    .catch(error => {
        showLoading(false);
        showAlert('Error fetching rankings: ' + error.message, 'error');
    });
}

function displayResults() {
    if (!currentData) {
        showAlert('No rankings data available', 'error');
        return;
    }
    
    const container = document.getElementById('results-container');
    const totalEntries = document.getElementById('total-entries');
    const rankingDate = document.getElementById('ranking-date');
    const status = document.getElementById('status');
    const storeBtn = document.getElementById('store-btn');
    
    if (totalEntries) totalEntries.textContent = currentData.total_entries;
    
    // Format the ranking date
    if (rankingDate) {
        const date = new Date(currentData.ranking_date);
        rankingDate.textContent = date.toLocaleDateString();
    }
    
    // Set status
    if (status) {
        if (currentData.already_exists) {
            status.textContent = 'Already exists';
            status.style.color = '#28a745';
            if (storeBtn) {
                storeBtn.disabled = true;
                storeBtn.value = 'Ranking Already Exists';
            }
        } else {
            status.textContent = 'New';
            status.style.color = '#007cba';
            if (storeBtn) {
                storeBtn.disabled = false;
                storeBtn.value = 'Store Rankings in Database';
            }
        }
    }
    
    if (container) {
        container.style.display = 'block';
    }
}

function togglePreview() {
    const previewContainer = document.getElementById('preview-container');
    const previewBtn = document.getElementById('preview-btn');
    
    if (previewContainer && previewBtn) {
        if (previewContainer.style.display === 'none') {
            showPreview();
            previewBtn.value = 'Hide Preview';
        } else {
            previewContainer.style.display = 'none';
            previewBtn.value = 'View Preview';
        }
    }
}

function showPreview() {
    if (!currentData || !currentData.items) {
        showAlert('No rankings data available for preview', 'error');
        return;
    }
    
    const tbody = document.getElementById('results-tbody');
    const previewContainer = document.getElementById('preview-container');
    
    if (!tbody || !previewContainer) return;
    
    tbody.innerHTML = '';
    
    // Show top 20 entries for preview
    const itemsToShow = currentData.items.slice(0, 20);
    
    itemsToShow.forEach((item, index) => {
        const row = document.createElement('tr');
        const songData = item.song || {};
        
        row.innerHTML = `
            <td>${item.position || 'N/A'}</td>
            <td>${songData.name || 'Unknown'}</td>
            <td>${songData.creditName || 'Unknown Artist'}</td>
            <td>${item.timeOnChart || 'N/A'}</td>
            <td>${formatPositionChange(item.positionEvolution)}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    if (currentData.items.length > 20) {
        const moreRow = document.createElement('tr');
        moreRow.innerHTML = `
            <td colspan="5" style="text-align: center; font-style: italic; color: #6c757d;">
                ... and ${currentData.items.length - 20} more entries
            </td>
        `;
        tbody.appendChild(moreRow);
    }
    
    previewContainer.style.display = 'block';
}

function formatPositionChange(change) {
    if (change === null || change === undefined) {
        return '🆕 New';
    } else if (change === 0) {
        return '→ No change';
    } else if (change > 0) {
        return `↑ +${change}`;
    } else {
        return `↓ ${Math.abs(change)}`;
    }
}

function storeRankings() {
    if (!currentData) {
        showAlert('No rankings data available to store', 'error');
        return;
    }
    
    if (currentData.already_exists) {
        showAlert('These rankings already exist in the database', 'error');
        return;
    }
    
    showLoading(true);
    
    const data = {
        ranking_date: currentData.ranking_date,
        items: currentData.items
    };
    
    // Construct the store rankings URL based on current path
    const storeUrl = window.location.pathname.replace('import-rankings/', 'api/store-rankings/');
    
    fetchData(storeUrl, {
        method: 'POST',
        body: JSON.stringify(data)
    })
    .then(data => {
        showLoading(false);
        if (data.success) {
            showAlert(data.message, 'success');
            // Update the status to show it's now stored
            const status = document.getElementById('status');
            if (status) {
                status.textContent = 'Stored';
                status.style.color = '#28a745';
            }
            
            const storeBtn = document.getElementById('store-btn');
            if (storeBtn) {
                storeBtn.disabled = true;
                storeBtn.value = 'Rankings Stored Successfully';
            }
            
            // Update the current data to reflect it's now stored
            currentData.already_exists = true;
            currentData.existing_ranking_id = data.ranking_id;
        } else {
            showAlert(data.error, 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        showAlert('Error storing rankings: ' + error.message, 'error');
    });
}

function clearResults() {
    currentData = null;
    currentCharts = null;
    
    // Clear charts results
    const chartsContainer = document.getElementById('chartsContainer');
    const chartsTable = document.getElementById('chartsTable');
    if (chartsContainer) chartsContainer.style.display = 'none';
    if (chartsTable) {
        const tbody = chartsTable.querySelector('tbody');
        if (tbody) tbody.innerHTML = '';
    }
    
    // Clear rankings results
    const resultsContainer = document.getElementById('results-container');
    const previewContainer = document.getElementById('preview-container');
    const rankingDate = document.getElementById('ranking_date');
    
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (previewContainer) previewContainer.style.display = 'none';
    if (rankingDate) rankingDate.value = '';
    
    // Show fetch section
    const fetchSection = document.getElementById('fetchSection');
    if (fetchSection) fetchSection.style.display = 'block';
    
    // Clear any alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());
}

// Utility function to hide alerts
function hideAlert() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for form submissions
    const fetchForm = document.getElementById('fetchForm');
    if (fetchForm) {
        fetchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            fetchCharts();
        });
    }
});
