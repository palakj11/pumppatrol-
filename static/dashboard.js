document.addEventListener('DOMContentLoaded', () => {
    loadStocks();
    startTelegramStream();

    // --- NEWS BUTTON LISTENER ---
    const btnNews = document.getElementById('btnNews');
    if (btnNews) {
        btnNews.addEventListener('click', () => {
            const ticker = document.getElementById('selectedTicker').innerText;
            if (ticker && ticker !== 'SELECT STOCK') {
                fetchAndShowNews(ticker);
            } else {
                alert("Please select and scan a stock first to fetch news.");
            }
        });
    }
});

let dashProfitChart = null;
let dashPromoterChart = null;

// --- 1. STOCK LIST LOADER ---
async function loadStocks() {
    try {
        const res = await fetch('/api/stocks');
        const data = await res.json();
        const tbody = document.getElementById('stockTableBody');
        document.getElementById('stockCount').innerText = data.length || 0;
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3">No stocks found.</td></tr>';
            return;
        }

        data.forEach(stock => {
            const tr = document.createElement('tr');
            tr.className = 'stock-row';
            tr.innerHTML = `
                <td style="color: var(--accent-green); font-weight:bold;">${stock.symbol}</td>
                <td style="color: #ccc;">${stock.name || 'N/A'}</td>
                <td class="action-cell">
                    <button class="btn-scan" onclick="loadStockDetails('${stock.symbol}')">SCAN</button>
                    <button class="btn-pdf" onclick="window.location.href='/generate_manual_pdf?y_ticker=${stock.symbol}'">📄 PDF</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) { console.error("Fetch Error:", err); }
}

// --- 2. TELEGRAM STREAM ---
async function startTelegramStream() {
    const container = document.getElementById('telegramList');
    setInterval(async () => {
        try {
            const res = await fetch('/api/telegram');
            const logs = await res.json();
            container.innerHTML = logs.map(l => `
                <div class="chat-bubble">
                    <div class="msg-text">${l.message_text}</div>
                    <div class="chat-time">${new Date(l.timestamp).toLocaleTimeString()}</div>
                </div>
            `).join('');
        } catch (e) { console.error(e); }
    }, 5000);
}

// --- 3. LOAD DETAILED ANALYSIS ---
async function loadStockDetails(symbol) {
    document.getElementById('detailPlaceholder').style.display = 'none';
    const view = document.getElementById('detailView');
    view.classList.remove('hidden');

    document.getElementById('selectedTicker').innerText = symbol;
    document.getElementById('detailVerdict').innerText = "SCANNING...";

    // Hide news button while scanning, show it after success
    const btnNews = document.getElementById('btnNews');
    if(btnNews) btnNews.style.display = 'none';

    try {
        const res = await fetch(`/api/stock_detail/${symbol}`);
        const data = await res.json();

        // A. Score & Verdict
        document.getElementById('detailScoreRing').innerText = data.score + "%";
        const verdictElem = document.getElementById('detailVerdict');
        const reasonBox = document.getElementById('detailReason');

        verdictElem.innerText = data.verdict;
        reasonBox.innerText = data.reason;

        if (data.score > 33) {
            verdictElem.className = "badge danger";
            reasonBox.style.borderColor = "#ff4d4d";
            reasonBox.style.color = "#ff9999";
        } else {
            verdictElem.className = "badge safe";
            reasonBox.style.borderColor = "#22c55e";
            reasonBox.style.color = "#d1fa5c";
        }

        // B. Stats & Table
        const ev = data.data;
        if(ev) {
            document.getElementById('detailVol').innerText = ev.volume ? ev.volume.toLocaleString() : '--';
            document.getElementById('detailEquity').innerText = ev.equity + " Cr";

            const tbody = document.getElementById('detailTableBody');
            tbody.innerHTML = `
                <tr><td>Net Profit</td><td>${ev.pat[0]}</td><td>${ev.pat[1]}</td><td>${ev.pat[2]}</td></tr>
                <tr><td>Cash Flow</td><td>${ev.cfo[0]}</td><td>${ev.cfo[1]}</td><td>${ev.cfo[2]}</td></tr>
                <tr><td>Promoter %</td><td>${ev.promoters[0]}</td><td>${ev.promoters[1]}</td><td>${ev.promoters[2]}</td></tr>
            `;

            // C. Render Charts
            renderDashboardCharts(ev);

            // D. Show News Button
            if(btnNews) btnNews.style.display = 'block';
        }
    } catch (err) { alert("Scan Failed: " + err); }
}

// --- 4. CHART RENDERING ---
function renderDashboardCharts(ev) {
    // 1. Profit Chart
    if(dashProfitChart) dashProfitChart.destroy();
    const ctx1 = document.getElementById('dashAuditChart').getContext('2d');
    dashProfitChart = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: ['Q1', 'Q2', 'Q3'],
            datasets: [
                { label: 'Profit', data: ev.pat, backgroundColor: '#22c55e' },
                { label: 'Cash', data: ev.cfo, backgroundColor: 'rgba(255, 77, 77, 0.5)' }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
    });

    // 2. Promoter Chart
    if(dashPromoterChart) dashPromoterChart.destroy();
    const ctx2 = document.getElementById('dashPromoterChart').getContext('2d');
    dashPromoterChart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: ['Q1', 'Q2', 'Q3'],
            datasets: [{ label: 'Promoter', data: ev.promoters, borderColor: '#8b5cf6', borderWidth: 2, pointRadius: 0 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
    });
}

// --- 5. NEWS FETCHING LOGIC ---
async function fetchAndShowNews(ticker) {
    const modal = document.getElementById('newsModal');
    const container = document.getElementById('newsContainer');

    // Show Modal with Loading State
    modal.style.display = 'flex';
    container.innerHTML = '<div style="padding:20px; text-align:center; color:#8b909a;">Fetching intel from Yahoo Finance...</div>';

    try {
        const res = await fetch(`/api/news/${ticker}`);
        const news = await res.json();

        container.innerHTML = ''; // Clear loading

        if (news.length === 0 || news.error) {
            container.innerHTML = '<div style="padding:20px; text-align:center; color:#8b909a;">No recent news found for this asset.</div>';
            return;
        }

        // Inject News Items
        news.forEach(item => {
            const timeAgo = new Date(item.providerPublishTime * 1000).toLocaleString();
            const div = document.createElement('div');
            div.className = 'news-item';
            div.innerHTML = `
                <a href="${item.link}" target="_blank">${item.title} ↗</a>
                <div class="news-meta">
                    <span>${item.publisher}</span>
                    <span>${timeAgo}</span>
                </div>
            `;
            container.appendChild(div);
        });

    } catch (err) {
        console.error(err);
        container.innerHTML = '<div style="padding:20px; text-align:center; color:#ff4d4d;">Failed to load news system.</div>';
    }
}

// --- 6. CLOSE MODAL HELPER ---
function closeNewsModal() {
    document.getElementById('newsModal').style.display = 'none';
}

// Close if clicked outside
window.onclick = function(event) {
    const modal = document.getElementById('newsModal');
    if (event.target === modal) {
        modal.style.display = "none";
    }
}