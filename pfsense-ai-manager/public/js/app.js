// API Base URL
const API_BASE = '/api';

// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Load tab data
    if (tabName === 'dashboard') {
        loadDashboard();
    }
}

// Load Dashboard
async function loadDashboard() {
    try {
        // Load system status
        const statusRes = await fetch(`${API_BASE}/system/status`);
        const statusData = await statusRes.json();
        document.getElementById('system-status').innerHTML = `
            <p><strong>Application:</strong> ${statusData.application}</p>
            <p><strong>Version:</strong> ${statusData.version}</p>
            <p><strong>Status:</strong> ✅ Online</p>
        `;

        // Load providers
        const providersRes = await fetch(`${API_BASE}/system/providers`);
        const providersData = await providersRes.json();
        let providersHTML = '<ul>';
        for (const [name, info] of Object.entries(providersData.providers)) {
            providersHTML += `<li>✅ ${name} (${info.model})</li>`;
        }
        providersHTML += '</ul>';
        document.getElementById('ai-providers').innerHTML = providersHTML;

        // Load threats
        const threatsRes = await fetch(`${API_BASE}/threats`);
        const threatsData = await threatsRes.json();
        const report = threatsData.report;
        document.getElementById('threat-summary').innerHTML = `
            <p><strong>Total Threats:</strong> ${report.threats_found}</p>
            <p>🔴 Critical: ${report.critical}</p>
            <p>🟠 High: ${report.high}</p>
            <p>🟡 Medium: ${report.medium}</p>
            <p>🟢 Low: ${report.low}</p>
        `;
    } catch (error) {
        console.error('Error loading dashboard:', error);
        document.getElementById('system-status').innerHTML = `<p>Error loading data</p>`;
    }
}

// Analyze Traffic
async function analyzeTraffic() {
    const resultsDiv = document.getElementById('traffic-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Analyzing traffic...';

    try {
        const res = await fetch(`${API_BASE}/analysis/traffic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timeframe: 'last_hour' })
        });
        const data = await res.json();

        let html = `<h3>Traffic Analysis Results</h3>`;
        html += `<p><strong>Timeframe:</strong> ${data.timeframe}</p>`;
        html += `<div class="card">
            <h4>Summary</h4>
            <p>${JSON.stringify(data.summary, null, 2)}</p>
        </div>`;
        html += `<div class="card">
            <h4>AI Analysis</h4>
            <p>${data.ai_analysis}</p>
        </div>`;

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Detect Threats
async function detectThreats() {
    const resultsDiv = document.getElementById('threats-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Scanning for threats...';

    try {
        const res = await fetch(`${API_BASE}/threats/dashboard`);
        const data = await res.json();

        const report = data.threats.report;
        let html = `<h3>Threat Detection Report</h3>`;
        html += `<div class="grid">
            <div class="card">
                <h4>Critical</h4>
                <p style="font-size: 24px; color: #d32f2f;">${report.critical}</p>
            </div>
            <div class="card">
                <h4>High</h4>
                <p style="font-size: 24px; color: #f57c00;">${report.high}</p>
            </div>
            <div class="card">
                <h4>Medium</h4>
                <p style="font-size: 24px; color: #fbc02d;">${report.medium}</p>
            </div>
            <div class="card">
                <h4>Low</h4>
                <p style="font-size: 24px; color: #388e3c;">${report.low}</p>
            </div>
        </div>`;

        if (report.threats.length > 0) {
            html += `<h4>Recent Threats</h4>`;
            html += `<ul>`;
            report.threats.slice(0, 10).forEach(threat => {
                html += `<li>${threat.type} (${threat.severity}): ${threat.message.substring(0, 80)}...</li>`;
            });
            html += `</ul>`;
        }

        if (report.ai_recommendation) {
            html += `<div class="card" style="margin-top: 20px;">
                <h4>AI Recommendation</h4>
                <p>${report.ai_recommendation}</p>
            </div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Analyze Configuration
async function analyzeConfig() {
    const resultsDiv = document.getElementById('config-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Analyzing configuration...';

    try {
        const res = await fetch(`${API_BASE}/config/analyze`, {
            method: 'POST'
        });
        const data = await res.json();

        let html = `<h3>Configuration Analysis</h3>`;
        html += `<div class="card">
            <h4>Rule Statistics</h4>
            <p><strong>Total Rules:</strong> ${data.total_rules}</p>
            <p><strong>Enabled:</strong> ${data.analysis.enabled_rules}</p>
            <p><strong>Disabled:</strong> ${data.analysis.disabled_rules}</p>
            <p><strong>Pass Rules:</strong> ${data.analysis.pass_rules}</p>
            <p><strong>Block Rules:</strong> ${data.analysis.block_rules}</p>
        </div>`;

        if (data.analysis.issues.length > 0) {
            html += `<div class="card" style="border-left-color: #ff9800;">
                <h4>Issues Found</h4>
                <ul>`;
            data.analysis.issues.forEach(issue => {
                html += `<li>[${issue.severity}] ${issue.message}</li>`;
            });
            html += `</ul></div>`;
        }

        if (data.ai_recommendations) {
            html += `<div class="card">
                <h4>AI Recommendations</h4>
                <p>${data.ai_recommendations}</p>
            </div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Get Recommendations
async function getRecommendations() {
    const resultsDiv = document.getElementById('config-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Getting recommendations...';

    try {
        const res = await fetch(`${API_BASE}/recommendations?type=security`);
        const data = await res.json();

        let html = `<h3>Configuration Recommendations</h3>`;

        if (data.recommendations.length > 0) {
            html += `<div class="card">
                <h4>Security Recommendations</h4>
                <ul>`;
            data.recommendations.forEach(rec => {
                html += `<li>[${rec.priority}] ${rec.recommendation}</li>`;
            });
            html += `</ul></div>`;
        }

        if (data.ai_insights) {
            html += `<div class="card">
                <h4>AI Insights</h4>
                <p>${data.ai_insights}</p>
            </div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Analyze Logs
async function analyzeLogs() {
    const resultsDiv = document.getElementById('logs-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Analyzing logs...';

    try {
        const res = await fetch(`${API_BASE}/logs/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 100 })
        });
        const data = await res.json();

        let html = `<h3>Log Analysis</h3>`;
        html += `<p><strong>Total Logs Analyzed:</strong> ${data.total_logs}</p>`;

        if (data.summary) {
            html += `<div class="card">
                <h4>Summary</h4>
                <p><strong>By Type:</strong></p>
                <ul>`;
            for (const [type, count] of Object.entries(data.summary.by_type)) {
                html += `<li>${type}: ${count}</li>`;
            }
            html += `</ul></div>`;
        }

        if (data.ai_analysis) {
            html += `<div class="card">
                <h4>AI Analysis</h4>
                <p>${data.ai_analysis}</p>
            </div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Search Logs
async function searchLogs() {
    const query = document.getElementById('log-search').value;
    if (!query) {
        alert('Please enter a search query');
        return;
    }

    const resultsDiv = document.getElementById('logs-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Searching logs...';

    try {
        const res = await fetch(`${API_BASE}/logs/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await res.json();

        let html = `<h3>Search Results for: "${query}"</h3>`;
        html += `<p><strong>Results Found:</strong> ${data.results_found}</p>`;

        if (data.ai_filter) {
            html += `<div class="card">
                <h4>AI Interpretation</h4>
                <p>${data.ai_filter}</p>
            </div>`;
        }

        if (data.logs && data.logs.length > 0) {
            html += `<div class="card">
                <h4>Matching Logs</h4>
                <ul>`;
            data.logs.forEach(log => {
                html += `<li>[${log.time}] ${log.msg}</li>`;
            });
            html += `</ul></div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Get Log Patterns
async function getLogPatterns() {
    const resultsDiv = document.getElementById('logs-results');
    resultsDiv.innerHTML = '<div class="loading"></div> Analyzing patterns...';

    try {
        const res = await fetch(`${API_BASE}/logs/patterns`);
        const data = await res.json();

        let html = `<h3>Log Pattern Analysis</h3>`;
        html += `<p><strong>Patterns Found:</strong> ${data.patterns_found}</p>`;

        if (data.patterns.length > 0) {
            html += `<div class="card">
                <h4>Top Patterns</h4>
                <ol>`;
            data.patterns.forEach(p => {
                html += `<li>${p.pattern.substring(0, 100)}... (${p.occurrences} times)</li>`;
            });
            html += `</ol></div>`;
        }

        if (data.ai_insights) {
            html += `<div class="card">
                <h4>AI Insights</h4>
                <p>${data.ai_insights}</p>
            </div>`;
        }

        resultsDiv.innerHTML = html;
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// Chat
async function sendChat() {
    const message = document.getElementById('chat-message').value;
    if (!message) return;

    const chatMessages = document.getElementById('chat-messages');
    
    // Add user message
    chatMessages.innerHTML += `<div class="chat-message user">${escapeHtml(message)}</div>`;
    document.getElementById('chat-message').value = '';

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await res.json();

        if (data.response) {
            chatMessages.innerHTML += `<div class="chat-message ai">${escapeHtml(data.response)}</div>`;
        } else {
            chatMessages.innerHTML += `<div class="chat-message ai">Error: ${data.error}</div>`;
        }

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        chatMessages.innerHTML += `<div class="chat-message ai" style="color: red;">Error: ${error.message}</div>`;
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load dashboard on page load
window.addEventListener('load', loadDashboard);
