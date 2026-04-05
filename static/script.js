let profitChart = null, promoterChart = null;

async function runAudit() {
    const sTicker = document.getElementById('sTicker').value;
    const yTicker = document.getElementById('yTicker').value;
    const resultsPanel = document.getElementById('scoreCard');
    const tablePanel = document.getElementById('tableCard');
    const verdictDisplay = document.getElementById('verdictBadge');
    const reasonBox = document.getElementById('reasonDisplay');

    resultsPanel.classList.remove('hidden');
    tablePanel.classList.remove('hidden');
    verdictDisplay.innerText = "SCANNING..."; verdictDisplay.className = "badge";

    try {
        const response = await fetch('/audit', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ s_ticker: sTicker, y_ticker: yTicker })
        });
        const data = await response.json();

        if (data.status === 'error') { alert(data.message); return; }

        document.getElementById('scoreDisplay').innerText = data.fraud_score + "%";
        document.getElementById('volDisplay').innerText = data.evidence.volume ? data.evidence.volume.toLocaleString() : '--';
        document.getElementById('equityDisplay').innerText = data.evidence.equity + " Cr";

        if (data.fraud_score > 33) {
            verdictDisplay.innerText = "HIGH RISK"; verdictDisplay.classList.add('danger');
            reasonBox.style.borderColor = "#ff4d4d"; reasonBox.style.color = "#ff9999";
        } else {
            verdictDisplay.innerText = "SAFE"; verdictDisplay.classList.add('safe');
            reasonBox.style.borderColor = "#22c55e"; reasonBox.style.color = "#d1fa5c";
        }
        reasonBox.innerText = data.reason;

        const tbody = document.getElementById('evidenceBody');
        const ev = data.evidence;
        tbody.innerHTML = `<tr><td>PAT</td><td>${ev.pat[0]}</td><td>${ev.pat[1]}</td><td>${ev.pat[2]}</td></tr>
                           <tr><td>CFO</td><td>${ev.cfo[0]}</td><td>${ev.cfo[1]}</td><td>${ev.cfo[2]}</td></tr>
                           <tr><td>Promoter</td><td>${ev.prom[0]}</td><td>${ev.prom[1]}</td><td>${ev.prom[2]}</td></tr>`;

        renderCharts(data.evidence);
    } catch (e) { console.error(e); }
}

function downloadManualPdf() {
    // For manual audit, we try to download data if it exists in DB
    const y = document.getElementById('yTicker').value;
    if(!y) { alert("Enter Yahoo Ticker First"); return; }
    window.open(`/generate_manual_pdf?y_ticker=${y}`, '_blank');
}

function renderCharts(ev) {
    if(profitChart) profitChart.destroy();
    profitChart = new Chart(document.getElementById('auditChart'), {
        type: 'bar', data: { labels: ['Q1','Q2','Q3'], datasets: [
            { label:'Profit', data: ev.pat, backgroundColor: '#22c55e' },
            { label:'Cash', data: ev.cfo, backgroundColor: 'rgba(255,77,77,0.5)' }
        ]}
    });

    if(promoterChart) promoterChart.destroy();
    promoterChart = new Chart(document.getElementById('promoterChart'), {
        type: 'line', data: { labels: ['Q1','Q2','Q3'], datasets: [{ label:'Promoter', data: ev.prom, borderColor:'#8b5cf6' }] }
    });
}