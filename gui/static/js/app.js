// Main Application
class WebsiteCheckerApp {
    constructor() {
        this.currentJobId = null;
        this.eventSource = null;
        this.charts = null;
        this.init();
    }

    init() {
        // Initialize components
        this.setupUploader();
        this.setupConfigureButton();
        this.setupStartProcessing();
        this.setupFilterButtons();
        this.setupExportButton();
    }

    setupUploader() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        // Drag and drop handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500', 'bg-blue-50');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');

            const file = e.dataTransfer.files[0];
            await this.uploadFile(file);
        });

        // File input change
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            await this.uploadFile(file);
        });

        // Click to browse
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    async uploadFile(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        // Show progress
        document.getElementById('upload-progress').classList.remove('hidden');

        try {
            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                alert(`Upload failed: ${result.detail}`);
                return;
            }

            // Store job ID
            this.currentJobId = result.job_id;

            // Show file info
            document.getElementById('file-name').textContent = result.filename;
            document.getElementById('url-count').textContent = result.url_count;
            document.getElementById('file-info').classList.remove('hidden');
            document.getElementById('upload-progress').classList.add('hidden');

        } catch (error) {
            console.error('Upload error:', error);
            alert('Upload failed. Please try again.');
            document.getElementById('upload-progress').classList.add('hidden');
        }
    }

    setupConfigureButton() {
        document.getElementById('configure-btn').addEventListener('click', () => {
            document.getElementById('config-section').classList.remove('hidden');
            document.getElementById('config-section').scrollIntoView({ behavior: 'smooth' });
        });
    }

    setupStartProcessing() {
        document.getElementById('start-processing-btn').addEventListener('click', async () => {
            const config = {
                batch_size: parseInt(document.getElementById('batch-size').value),
                concurrent: parseInt(document.getElementById('concurrent').value),
                timeout: parseInt(document.getElementById('timeout').value),
                url_column: document.getElementById('url-column').value,
                include_inactive: document.getElementById('include-inactive').checked,
                include_errors: document.getElementById('include-errors').checked
            };

            try {
                const response = await fetch(`/api/process/start/${this.currentJobId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                if (!response.ok) {
                    alert('Failed to start processing');
                    return;
                }

                // Show processing section
                document.getElementById('processing-section').classList.remove('hidden');
                document.getElementById('processing-section').scrollIntoView({ behavior: 'smooth' });

                // Initialize charts
                this.charts = new ChartManager();

                // Connect to SSE
                this.connectSSE();

            } catch (error) {
                console.error('Processing error:', error);
                alert('Failed to start processing');
            }
        });
    }

    connectSSE() {
        this.eventSource = new EventSource(`/api/sse/progress/${this.currentJobId}`);

        this.eventSource.onmessage = (event) => {
            const progress = JSON.parse(event.data);

            if (progress.error) {
                this.eventSource.close();
                alert('Error: ' + progress.error);
                return;
            }

            this.updateProgress(progress);
            this.charts.update(progress);

            if (progress.status === 'completed' || progress.status === 'failed') {
                this.eventSource.close();
                if (progress.status === 'completed') {
                    this.loadResults();
                } else {
                    alert('Processing failed: ' + (progress.errors || []). join(', '));
                }
            }
        };

        this.eventSource.onerror = () => {
            console.error('SSE connection error');
            this.eventSource.close();
        };
    }

    updateProgress(progress) {
        const percentage = progress.total_urls > 0
            ? (progress.processed_urls / progress.total_urls) * 100
            : 0;

        document.getElementById('progress-bar').style.width = `${percentage}%`;
        document.getElementById('progress-percent').textContent = `${percentage.toFixed(1)}%`;
        document.getElementById('progress-text').textContent =
            `${progress.processed_urls} / ${progress.total_urls} URLs processed`;

        document.getElementById('stat-active').textContent = progress.active_count;
        document.getElementById('stat-inactive').textContent = progress.inactive_count;
        document.getElementById('stat-errors').textContent = progress.error_count;
        document.getElementById('stat-rate').textContent = `${progress.processing_rate.toFixed(1)}/s`;

        const eta = this.formatETA(progress.eta_seconds);
        document.getElementById('stat-eta').textContent = eta;
    }

    formatETA(seconds) {
        if (!seconds || seconds <= 0) return '--:--';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    async loadResults() {
        document.getElementById('results-section').classList.remove('hidden');
        await this.fetchResults(1);
    }

    async fetchResults(page = 1, filter = '') {
        const url = `/api/results/${this.currentJobId}?page=${page}&limit=50${filter ? '&filter_status=' + filter : ''}`;
        const response = await fetch(url);
        const data = await response.json();

        const tbody = document.getElementById('results-tbody');
        tbody.innerHTML = '';

        data.results.forEach(result => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.url}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs rounded-full ${this.getStatusClass(result.status_result)}">
                        ${result.status_result}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.status_code || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.response_time?.toFixed(2) || '-'}s</td>
                <td class="px-6 py-4 text-sm text-gray-500">${result.error_message || '-'}</td>
            `;
        });
    }

    getStatusClass(status) {
        const classes = {
            'active': 'bg-green-100 text-green-800',
            'inactive': 'bg-orange-100 text-orange-800',
            'error': 'bg-red-100 text-red-800',
            'timeout': 'bg-red-100 text-red-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    }

    setupFilterButtons() {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Update active state
                document.querySelectorAll('.filter-btn').forEach(b => {
                    b.classList.remove('active', 'bg-blue-100', 'text-blue-700');
                    b.classList.add('bg-gray-100', 'text-gray-700');
                });
                e.target.classList.add('active', 'bg-blue-100', 'text-blue-700');
                e.target.classList.remove('bg-gray-100', 'text-gray-700');

                // Fetch filtered results
                const filter = e.target.dataset.filter;
                this.fetchResults(1, filter);
            });
        });
    }

    setupExportButton() {
        document.getElementById('export-btn').addEventListener('click', () => {
            window.location.href = `/api/results/${this.currentJobId}/export?format=csv`;
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new WebsiteCheckerApp();
});
