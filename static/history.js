let backtestChart = null;

async function runBacktest() {
    const ticker = document.getElementById('histTicker').value;
    const start = document.getElementById('startDate').value;
    const end = document.getElementById('endDate').value;
    const panel = document.getElementById('resultPanel');

    if (!ticker || !start || !end) {
        alert("Please fill in all fields.");
        return;
    }

    // Show Loading
    panel.classList.remove('hidden');
    document.getElementById('pastVerdict').innerText = "ANALYZING...";

    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, start, end })
        });

        const data = await response.json();

        if (data.status === 'error') {
            alert(data.message);
            return;
        }

        // 1. UPDATE VERDICT
        const verdictElem = document.getElementById('pastVerdict');
        const scoreElem = document.getElementById('pastScore');
        const reasonElem = document.getElementById('pastReason');

        verdictElem.innerText = data.verdict;
        scoreElem.innerText = data.fraud_score + "%";
        reasonElem.innerText = data.reason;

        if (data.fraud_score > 50) {
            verdictElem.style.color = "#ff4d4d"; // Red
            scoreElem.style.color = "#ff4d4d";
        } else {
            verdictElem.style.color = "#22c55e"; // Green
            scoreElem.style.color = "#22c55e";
        }

        // 2. RENDER CHART
        renderTimelineChart(data.history_dates, data.history_prices, end);

    } catch (e) {
        console.error(e);
        alert("Backtest failed. Check console.");
    }
}

function renderTimelineChart(dates, prices, splitDate) {
    const ctx = document.getElementById('backtestChart').getContext('2d');

    if (backtestChart) backtestChart.destroy();

    // Create an annotation line for the "Verdict Date"
    // Note: We use simple coloring logic here.

    const splitIndex = dates.findIndex(d => d >= splitDate);

    // Create color array: Green/Gray before split, Red after split (if crash)
    const segmentColors = prices.map((p, i) => i < splitIndex ? '#3b82f6' : '#ff4d4d');

    backtestChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Stock Price',
                data: prices,
                borderColor: '#8b909a', // Base line color
                segment: {
                    borderColor: ctx => ctx.p0DataIndex < splitIndex ? '#3b82f6' : '#ff4d4d',
                    borderWidth: 2
                },
                pointRadius: 0,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: false },
                annotation: { // Requires Chartjs annotation plugin, but we'll stick to basic visual
                    // Simple title logic
                    title: { display: true, text: 'Blue: Analysis Period | Red: What Happened After', color: '#666' }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#666' } },
                y: { grid: { color: '#222' }, ticks: { color: '#666' } }
            }
        }
    });
}