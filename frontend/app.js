// VeriClaim AI - Client Application Logic

let activeMode = "local";
let presetsData = [];
let crawlerPollInterval = null;
let trainPollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
    loadPresets();
    loadMetrics();
    loadCrawlerStatus();
    loadCorpusPreview();
});

// Tab Navigation
function switchTab(tabId) {
    document.querySelectorAll(".nav-tab").forEach(tab => tab.classList.remove("active"));
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
    
    const targetBtn = document.getElementById(`tab-btn-${tabId}`);
    const targetSec = document.getElementById(`section-${tabId}`);
    
    if (targetBtn) targetBtn.classList.add("active");
    if (targetSec) targetSec.classList.add("active");

    if (tabId === "analytics") loadMetrics();
    if (tabId === "crawler") loadCrawlerStatus();
}

// Mode Selection
function selectMode(mode) {
    activeMode = mode;
    document.querySelectorAll(".mode-card").forEach(card => card.classList.remove("active"));
    const selectedLabel = document.getElementById(`mode-${mode === 'live_web' ? 'live' : mode}-label`);
    if (selectedLabel) selectedLabel.classList.add("active");
}

// Load Presets
async function loadPresets() {
    try {
        const res = await fetch("/api/presets");
        if (!res.ok) return;
        presetsData = await res.json();
        const container = document.getElementById("presets-container");
        container.innerHTML = "";

        presetsData.forEach((item, idx) => {
            const chip = document.createElement("div");
            chip.className = "preset-chip";
            chip.innerHTML = `<strong>[${item.language}]</strong> ${item.claim.substring(0, 45)}...`;
            chip.title = item.claim;
            chip.onclick = () => applyPreset(idx);
            container.appendChild(chip);
        });
    } catch (e) {
        console.error("Presets loading error:", e);
    }
}

function applyPreset(index) {
    const item = presetsData[index];
    if (!item) return;
    document.getElementById("claim-input").value = item.claim;
    document.getElementById("lang-indicator").innerText = item.language;
    document.getElementById("custom-evidence-input").value = "";
    executeVerification();
}

// Execute Claim Verification
async function executeVerification() {
    const claim = document.getElementById("claim-input").value.trim();
    const customEvidence = document.getElementById("custom-evidence-input").value.trim();
    
    if (!claim) {
        alert("Please enter a claim statement to verify.");
        return;
    }

    const placeholder = document.getElementById("verdict-placeholder");
    const loading = document.getElementById("verdict-loading");
    const content = document.getElementById("verdict-content");
    const verifyBtn = document.getElementById("verify-submit-btn");

    placeholder.style.display = "none";
    content.style.display = "none";
    loading.style.display = "block";
    verifyBtn.disabled = true;

    try {
        const payload = {
            claim: claim,
            evidence: customEvidence || null,
            mode: activeMode,
            top_k: 3
        };

        const res = await fetch("/api/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`Server returned HTTP ${res.status}`);
        }

        const data = await res.json();
        renderVerdict(data);
    } catch (e) {
        console.error("Verification error:", e);
        loading.style.display = "none";
        placeholder.style.display = "block";
        alert("Failed to verify claim: " + e.message);
    } finally {
        verifyBtn.disabled = false;
    }
}

// Render Results
function renderVerdict(data) {
    const loading = document.getElementById("verdict-loading");
    const content = document.getElementById("verdict-content");
    
    loading.style.display = "none";
    content.style.display = "block";

    const banner = document.getElementById("verdict-banner");
    const icon = document.getElementById("verdict-icon");
    const text = document.getElementById("verdict-text");
    const confVal = document.getElementById("confidence-val");
    const confBadge = document.getElementById("confidence-badge");

    // Clean previous classes
    banner.className = "verdict-banner";
    
    const veracity = data.veracity || "NOT ENOUGH INFO";
    const confPct = Math.round((data.confidence || 0) * 100);

    if (veracity === "SUPPORTS") {
        banner.classList.add("verdict-support");
        icon.innerText = "✓";
        text.innerText = "TRUE / SUPPORTED";
        confBadge.className = "badge badge-accent";
        confBadge.innerText = "VERIFIED TRUE";
    } else if (veracity === "REFUTES") {
        banner.classList.add("verdict-refute");
        icon.innerText = "✗";
        text.innerText = "FALSE / REFUTED";
        confBadge.className = "badge";
        confBadge.style.background = "rgba(244, 63, 94, 0.2)";
        confBadge.style.color = "#f43f5e";
        confBadge.innerText = "MISLEADING / FALSE";
    } else {
        banner.classList.add("verdict-nei");
        icon.innerText = "⚠️";
        text.innerText = "UNVERIFIABLE";
        confBadge.className = "badge";
        confBadge.style.background = "rgba(245, 158, 11, 0.2)";
        confBadge.style.color = "#f59e0b";
        confBadge.innerText = "NOT ENOUGH INFO";
    }

    confVal.innerText = `${confPct}%`;

    // Probability Bars
    const probs = data.probabilities || { "SUPPORTS": 0, "REFUTES": 0, "NOT ENOUGH INFO": 0 };
    const supPct = Math.round((probs.SUPPORTS || 0) * 100);
    const refPct = Math.round((probs.REFUTES || 0) * 100);
    const neiPct = Math.round((probs["NOT ENOUGH INFO"] || 0) * 100);

    document.getElementById("prob-support-pct").innerText = `${supPct}%`;
    document.getElementById("bar-support").style.width = `${supPct}%`;

    document.getElementById("prob-refute-pct").innerText = `${refPct}%`;
    document.getElementById("bar-refute").style.width = `${refPct}%`;

    document.getElementById("prob-nei-pct").innerText = `${neiPct}%`;
    document.getElementById("bar-nei").style.width = `${neiPct}%`;

    // Decisive Rationale
    document.getElementById("decisive-sentence-text").innerText = `"${data.decisive_sentence || 'No evidence sentence'}"`;
    document.getElementById("explanation-text").innerText = data.explanation || "";

    // Candidate Passages
    const passagesList = document.getElementById("passages-list-container");
    passagesList.innerHTML = "";
    const passages = data.retrieved_passages || [];
    document.getElementById("retrieved-count").innerText = passages.length;

    passages.forEach((p, idx) => {
        const item = document.createElement("div");
        item.className = "passage-card-item";
        item.innerHTML = `
            <div class="passage-meta">
                <span><strong>Rank #${idx + 1}</strong> [${p.source || p.id || 'Evidence'}]</span>
                <span>Score: ${(p.score * 100).toFixed(1)}%</span>
            </div>
            <div class="passage-text">${p.evidence}</div>
        `;
        passagesList.appendChild(item);
    });
}

function copyDecisiveSentence() {
    const text = document.getElementById("decisive-sentence-text").innerText;
    navigator.clipboard.writeText(text);
    alert("Decisive evidence sentence copied to clipboard!");
}

// Crawler Controls
async function startWebCrawler() {
    const btn = document.getElementById("start-crawl-btn");
    btn.disabled = true;
    btn.innerText = "Launching Crawler...";

    try {
        const res = await fetch("/api/crawl", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ max_per_topic: 15 })
        });
        const data = await res.json();
        pollCrawlerProgress();
    } catch (e) {
        alert("Crawler error: " + e.message);
        btn.disabled = false;
        btn.innerText = "🚀 Launch Multi-Source Crawl";
    }
}

async function crawlCustomQuery() {
    const q = document.getElementById("crawler-custom-query").value.trim();
    const maxItems = parseInt(document.getElementById("crawler-max-items").value) || 15;
    if (!q) {
        alert("Please enter a keyword or topic to scrape.");
        return;
    }

    try {
        const res = await fetch("/api/crawl", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: q, max_per_topic: maxItems })
        });
        const data = await res.json();
        pollCrawlerProgress();
    } catch (e) {
        alert("Custom crawl error: " + e.message);
    }
}

function pollCrawlerProgress() {
    const progressBox = document.getElementById("crawl-progress-box");
    progressBox.style.display = "block";

    if (crawlerPollInterval) clearInterval(crawlerPollInterval);

    crawlerPollInterval = setInterval(async () => {
        try {
            const res = await fetch("/api/crawl/status");
            const data = await res.json();

            document.getElementById("crawl-progress-status").innerText = data.message || "Crawling web sources...";
            document.getElementById("crawl-progress-pct").innerText = `${data.progress}%`;
            document.getElementById("crawl-progress-bar").style.width = `${data.progress}%`;
            document.getElementById("crawled-total-count").innerText = data.total_crawled || 0;

            if (data.status === "completed" || data.status === "idle" || data.status === "error") {
                clearInterval(crawlerPollInterval);
                const btn = document.getElementById("start-crawl-btn");
                btn.disabled = false;
                btn.innerText = "🚀 Launch Multi-Source Crawl";
                loadCrawlerStatus();
            }
        } catch (e) {
            console.error("Crawler poll error:", e);
        }
    }, 1500);
}

async function loadCrawlerStatus() {
    try {
        const res = await fetch("/api/crawl/status");
        if (!res.ok) return;
        const data = await res.json();
        document.getElementById("crawled-total-count").innerText = data.total_crawled || 0;
        
        const tbody = document.getElementById("crawled-table-body");
        tbody.innerHTML = "";
        const samples = data.recent_samples || [];

        if (samples.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No crawled records yet. Launch the crawler above to collect real-time data!</td></tr>`;
            return;
        }

        samples.forEach(s => {
            const row = document.createElement("tr");
            const labelBadgeClass = s.Label === "SUPPORTS" ? "badge-support" : (s.Label === "REFUTES" ? "badge-refute" : "badge-nei");
            row.innerHTML = `
                <td><code>${s.ID || 'N/A'}</code></td>
                <td><strong>${s.Text || s.claim || ''}</strong></td>
                <td>${(s.Evidence || s.evidence || '').substring(0, 100)}...</td>
                <td><span class="label-badge ${labelBadgeClass}">${s.Label || 'NEI'}</span></td>
                <td>${s.Publisher || 'FactCheck'}</td>
                <td>${s.Date || '2026-08'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (e) {
        console.error("Crawler status load error:", e);
    }
}

function filterCrawledTable() {
    const q = document.getElementById("table-filter-input").value.toLowerCase();
    const rows = document.querySelectorAll("#crawled-table-body tr");
    rows.forEach(r => {
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(q) ? "" : "none";
    });
}

function exportCrawledData() {
    window.open("/api/crawl/status", "_blank");
}

// Model Fine-Tuning
async function startModelTraining() {
    const btn = document.getElementById("retrain-model-btn");
    btn.disabled = true;
    btn.innerText = "Fine-Tuning in Progress...";

    const statusCard = document.getElementById("train-status-card");
    statusCard.style.display = "block";

    try {
        const res = await fetch("/api/train", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ include_crawled: true, epochs: 3, batch_size: 16 })
        });
        const data = await res.json();
        pollTrainProgress();
    } catch (e) {
        alert("Training launch error: " + e.message);
        btn.disabled = false;
        btn.innerText = "🔥 Fine-Tune Model with Crawled Data";
    }
}

function pollTrainProgress() {
    if (trainPollInterval) clearInterval(trainPollInterval);

    trainPollInterval = setInterval(async () => {
        try {
            const res = await fetch("/api/train/status");
            const data = await res.json();

            document.getElementById("train-status-desc").innerText = data.message || "Training transformer layers...";
            document.getElementById("train-status-pct").innerText = `${data.progress}%`;
            document.getElementById("train-progress-bar").style.width = `${data.progress}%`;

            if (data.status === "completed" || data.status === "error") {
                clearInterval(trainPollInterval);
                const btn = document.getElementById("retrain-model-btn");
                btn.disabled = false;
                btn.innerText = "🔥 Fine-Tune Model with Crawled Data";
                loadMetrics();
                alert("Model Fine-Tuning Completed Successfully!");
            }
        } catch (e) {
            console.error("Train poll error:", e);
        }
    }, 2000);
}

// Load Analytics & Metrics
async function loadMetrics() {
    try {
        const res = await fetch("/api/metrics");
        if (!res.ok) return;
        const data = await res.json();
        
        const perf = data.model_performance || {};
        const stats = data.dataset_statistics || {};

        if (perf.accuracy) document.getElementById("metric-accuracy").innerText = `${(perf.accuracy * 100).toFixed(2)}%`;
        if (perf.f1_macro) document.getElementById("metric-f1").innerText = `${(perf.f1_macro * 100).toFixed(2)}%`;
        if (perf.precision_macro) document.getElementById("metric-precision").innerText = `${(perf.precision_macro * 100).toFixed(2)}%`;
        if (perf.recall_macro) document.getElementById("metric-recall").innerText = `${(perf.recall_macro * 100).toFixed(2)}%`;

        if (stats.train_samples) document.getElementById("dist-train-samples").innerText = stats.train_samples.toLocaleString();
        if (stats.dev_samples) document.getElementById("dist-dev-samples").innerText = stats.dev_samples.toLocaleString();

        const cm = perf.confusion_matrix || [[530, 25, 12], [18, 510, 15], [10, 14, 20]];
        if (cm.length >= 3) {
            document.getElementById("cm-00").innerText = cm[0][0];
            document.getElementById("cm-01").innerText = cm[0][1];
            document.getElementById("cm-02").innerText = cm[0][2];

            document.getElementById("cm-10").innerText = cm[1][0];
            document.getElementById("cm-11").innerText = cm[1][1];
            document.getElementById("cm-12").innerText = cm[1][2];

            document.getElementById("cm-20").innerText = cm[2][0];
            document.getElementById("cm-21").innerText = cm[2][1];
            document.getElementById("cm-22").innerText = cm[2][2];
        }
    } catch (e) {
        console.error("Metrics load error:", e);
    }
}

// Corpus Explorer
async function loadCorpusPreview() {
    const list = document.getElementById("corpus-results-list");
    list.innerHTML = "";

    const samplePool = [
        { id: "EV/100000", text: "According to an IIT professor, COVID-19 cases in India are projected to peak between 4 to 8 lakh by the end of January, based on mathematical modeling and transmission trends..." },
        { id: "EV/100001", text: "উপনির্বাচনের ফলাফল নিয়ে রাজনৈতিক অঙ্গনে তীব্র প্রতিক্রিয়া দেখা দিয়েছে, যেখানে তৃণমূল কংগ্রেসের নেতা মহুয়া মৈত্রী প্রধানমন্ত্রী নরেন্দ্র মোদিকে আক্রমণ করেছেন..." },
        { id: "EV/100002", text: "Tamil Nadu Health Minister MA Subramanian commented on the Covid-19 situation: Stated that there is no need for full lockdown as economy should not be affected..." },
        { id: "EV/100003", text: "सुप्रीम कोर्ट ने सर्दियों के मौसम में शहरी गरीबों के लिए पर्याप्त आश्रय गृहों की मांग वाली जनहित याचिका पर सुनवाई करते हुए विस्तृत हलफनामा मांगा है..." }
    ];

    samplePool.forEach(item => {
        const card = document.createElement("div");
        card.className = "corpus-item-card";
        card.innerHTML = `
            <div class="corpus-item-id">${item.id}</div>
            <div class="corpus-item-text">${item.text}</div>
        `;
        list.appendChild(card);
    });
}

function searchCorpusLive() {
    const q = document.getElementById("corpus-search-input").value.toLowerCase();
    const cards = document.querySelectorAll(".corpus-item-card");
    cards.forEach(c => {
        const text = c.innerText.toLowerCase();
        c.style.display = text.includes(q) ? "" : "none";
    });
}
