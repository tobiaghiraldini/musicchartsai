// Admin Data Table JavaScript
class AdminDataTable {
    constructor(tableId, data, options = {}) {
        this.table = document.getElementById(tableId);
        this.data = data;
        this.options = {
            pageSize: options.pageSize || 25,
            sortable: options.sortable !== false,
            searchable: options.searchable !== false,
            ...options
        };
        
        this.currentPage = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.filteredData = [...this.data];
        
        this.init();
    }
    
    init() {
        this.createTable();
        this.bindEvents();
        this.render();
    }
    
    createTable() {
        const thead = this.table.querySelector('thead');
        const tbody = this.table.querySelector('tbody');
        
        // Clear existing content
        thead.innerHTML = '';
        tbody.innerHTML = '';
        
        // Create header row
        const headerRow = document.createElement('tr');
        const headers = [
            { key: 'position', label: 'Position', sortable: true, width: '80px' },
            { key: 'track_name', label: 'Track & Artist', sortable: true, width: '35%' },
            { key: 'trend_text', label: 'Trend', sortable: true, width: '15%' },
            { key: 'weeks', label: 'Weeks', sortable: true, width: '10%' },
            { key: 'streams', label: 'Streams', sortable: true, width: '20%' },
            { key: 'previous_position', label: 'Previous', sortable: true, width: '10%' }
        ];
        
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header.label;
            th.style.width = header.width;
            
            if (header.sortable && this.options.sortable) {
                th.classList.add('sortable');
                th.dataset.key = header.key;
            }
            
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
    }
    
    bindEvents() {
        // Sort events
        if (this.options.sortable) {
            this.table.addEventListener('click', (e) => {
                if (e.target.classList.contains('sortable')) {
                    this.handleSort(e.target.dataset.key);
                }
            });
        }
        
        // Search events
        if (this.options.searchable) {
            const searchBox = document.getElementById('searchBox');
            if (searchBox) {
                searchBox.addEventListener('input', (e) => {
                    this.handleSearch(e.target.value);
                });
            }
        }
    }
    
    handleSort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        
        this.sortData();
        this.updateSortIndicators();
        this.render();
    }
    
    sortData() {
        this.filteredData.sort((a, b) => {
            let aVal = a[this.sortColumn];
            let bVal = b[this.sortColumn];
            
            // Handle numeric values
            if (this.sortColumn === 'position' || this.sortColumn === 'weeks' || this.sortColumn === 'streams') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            }
            
            // Handle string values
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.sortDirection === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }
    
    updateSortIndicators() {
        // Clear all sort indicators
        this.table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add current sort indicator
        if (this.sortColumn) {
            const currentHeader = this.table.querySelector(`th[data-key="${this.sortColumn}"]`);
            if (currentHeader) {
                currentHeader.classList.add(this.sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
            }
        }
    }
    
    handleSearch(query) {
        if (!query) {
            this.filteredData = [...this.data];
        } else {
            const lowerQuery = query.toLowerCase();
            this.filteredData = this.data.filter(item => 
                item.track_name.toLowerCase().includes(lowerQuery) ||
                item.artist_name.toLowerCase().includes(lowerQuery) ||
                item.trend_text.toLowerCase().includes(lowerQuery) ||
                item.position.toString().includes(lowerQuery)
            );
        }
        
        this.currentPage = 1;
        this.render();
    }
    
    render() {
        const tbody = this.table.querySelector('tbody');
        tbody.innerHTML = '';
        
        const startIndex = (this.currentPage - 1) * this.options.pageSize;
        const endIndex = startIndex + this.options.pageSize;
        const pageData = this.filteredData.slice(startIndex, endIndex);
        
        pageData.forEach(item => {
            const row = document.createElement('tr');
            
            // Position
            const positionCell = document.createElement('td');
            positionCell.className = 'position';
            positionCell.textContent = item.position;
            row.appendChild(positionCell);
            
            // Track & Artist
            const trackCell = document.createElement('td');
            trackCell.className = 'track-info';
            trackCell.style.wordWrap = 'break-word';
            trackCell.style.overflowWrap = 'break-word';
            trackCell.innerHTML = `
                <a href="${item.track_url}" class="track-name" style="word-wrap: break-word; overflow-wrap: break-word; display: block;">${item.track_name}</a>
                <span class="artist-name" style="word-wrap: break-word; overflow-wrap: break-word; display: block;">${item.artist_name}</span>
            `;
            row.appendChild(trackCell);
            
            // Trend
            const trendCell = document.createElement('td');
            trendCell.className = `trend ${item.trend_class}`;
            trendCell.innerHTML = `${item.trend_icon} ${item.trend_text}`;
            row.appendChild(trendCell);
            
            // Weeks
            const weeksCell = document.createElement('td');
            weeksCell.className = 'weeks';
            weeksCell.textContent = item.weeks;
            row.appendChild(weeksCell);
            
            // Streams
            const streamsCell = document.createElement('td');
            streamsCell.className = 'streams';
            streamsCell.textContent = item.streams;
            row.appendChild(streamsCell);
            
            // Previous Position
            const prevCell = document.createElement('td');
            prevCell.className = 'previous-position';
            prevCell.textContent = item.previous_position;
            row.appendChild(prevCell);
            
            tbody.appendChild(row);
        });
        
        this.updatePagination();
        this.updateTableInfo();
    }
    
    updatePagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;
        
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        const startItem = (this.currentPage - 1) * this.options.pageSize + 1;
        const endItem = Math.min(this.currentPage * this.options.pageSize, this.filteredData.length);
        
        pagination.innerHTML = `
            <div class="table-info">
                Showing ${startItem} to ${endItem} of ${this.filteredData.length} entries
            </div>
            <div class="pagination-controls">
                <button class="pagination-btn" onclick="dataTable.goToPage(1)" ${this.currentPage === 1 ? 'disabled' : ''}>
                    « First
                </button>
                <button class="pagination-btn" onclick="dataTable.goToPage(${this.currentPage - 1})" ${this.currentPage === 1 ? 'disabled' : ''}>
                    ‹ Previous
                </button>
                ${this.generatePageNumbers(totalPages)}
                <button class="pagination-btn" onclick="dataTable.goToPage(${this.currentPage + 1})" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    Next ›
                </button>
                <button class="pagination-btn" onclick="dataTable.goToPage(${totalPages})" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    Last »
                </button>
            </div>
        `;
    }
    
    generatePageNumbers(totalPages) {
        let pages = '';
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            pages += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" onclick="dataTable.goToPage(${i})">
                    ${i}
                </button>
            `;
        }
        
        return pages;
    }
    
    updateTableInfo() {
        const tableInfo = document.getElementById('tableInfo');
        if (tableInfo) {
            tableInfo.textContent = `Showing ${this.filteredData.length} of ${this.data.length} entries`;
        }
    }
    
    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.render();
        }
    }
}

// Mini table functionality for admin tabs
class MiniDataTable {
    constructor(rankingId) {
        this.rankingId = rankingId;
        this.currentSort = { column: 'position', direction: 'asc' };
        this.init();
    }
    
    init() {
        this.bindEvents();
    }
    
    bindEvents() {
        // Sort events
        const headers = document.querySelectorAll(`#entriesTable_${this.rankingId} th`);
        headers.forEach((header, index) => {
            header.addEventListener('click', () => {
                const columnMap = ['position', 'track', 'trend', 'weeks', 'streams', 'previous'];
                this.handleSort(columnMap[index]);
            });
        });
        
        // Search functionality
        const searchBox = document.getElementById(`searchBox_${this.rankingId}`);
        if (searchBox) {
            searchBox.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
    }
    
    handleSort(column) {
        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }
        
        this.sortData(column);
        this.updateSortIndicators(column);
    }
    
    sortData(column) {
        const table = document.getElementById(`entriesTable_${this.rankingId}`);
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            let aVal, bVal;
            
            if (column === 'position' || column === 'weeks' || column === 'streams') {
                aVal = parseInt(a.cells[column === 'position' ? 0 : column === 'weeks' ? 3 : 4].textContent) || 0;
                bVal = parseInt(b.cells[column === 'position' ? 0 : column === 'weeks' ? 3 : 4].textContent) || 0;
            } else {
                aVal = a.cells[column === 'track' ? 1 : column === 'trend' ? 2 : 5].textContent.toLowerCase();
                bVal = b.cells[column === 'track' ? 1 : column === 'trend' ? 2 : 5].textContent.toLowerCase();
            }
            
            if (this.currentSort.direction === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
        
        // Reorder rows
        rows.forEach(row => tbody.appendChild(row));
    }
    
    updateSortIndicators(column) {
        const table = document.getElementById(`entriesTable_${this.rankingId}`);
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            const columnMap = ['position', 'track', 'trend', 'weeks', 'streams', 'previous'];
            if (columnMap[index] === column) {
                header.innerHTML = header.innerHTML.replace(' ↕', '') + 
                    (this.currentSort.direction === 'asc' ? ' ↑' : ' ↓');
            } else {
                header.innerHTML = header.innerHTML.replace(/ [↑↓]/, '') + ' ↕';
            }
        });
    }
    
    handleSearch(query) {
        const table = document.getElementById(`entriesTable_${this.rankingId}`);
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(query.toLowerCase())) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        const tableInfo = document.getElementById(`tableInfo_${this.rankingId}`);
        if (tableInfo) {
            tableInfo.textContent = `Showing ${visibleCount} of ${rows.length} entries`;
        }
    }
}

// Initialize data table when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the full entries page
    const entriesTable = document.getElementById('entriesTable');
    if (entriesTable && window.tableData) {
        window.dataTable = new AdminDataTable('entriesTable', window.tableData, {
            pageSize: 25,
            sortable: true,
            searchable: true
        });
    }
    
    // Check if we're on the admin tab with mini table
    const miniTables = document.querySelectorAll('[id^="entriesTable_"]');
    miniTables.forEach(table => {
        const rankingId = table.id.replace('entriesTable_', '');
        new MiniDataTable(rankingId);
    });
});
