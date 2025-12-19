// Chart Manager
class ChartManager {
    constructor() {
        this.statusChart = this.createStatusChart();
        this.rateChart = this.createRateChart();
        this.rateData = [];
    }

    createStatusChart() {
        const ctx = document.getElementById('status-chart').getContext('2d');
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Active', 'Inactive', 'Errors'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        '#10b981',  // Green
                        '#f59e0b',  // Orange
                        '#ef4444'   // Red
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    title: {
                        display: false
                    }
                }
            }
        });
    }

    createRateChart() {
        const ctx = document.getElementById('rate-chart').getContext('2d');
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'URLs/sec',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Processing Rate'
                        }
                    },
                    x: {
                        display: false
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    update(progress) {
        // Update status chart
        this.statusChart.data.datasets[0].data = [
            progress.active_count,
            progress.inactive_count,
            progress.error_count
        ];
        this.statusChart.update('none'); // 'none' for no animation

        // Update rate chart
        this.rateData.push(progress.processing_rate);
        if (this.rateData.length > 50) {
            this.rateData.shift();
        }

        this.rateChart.data.labels = this.rateData.map((_, i) => i);
        this.rateChart.data.datasets[0].data = this.rateData;
        this.rateChart.update('none');
    }
}
