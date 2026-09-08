/**
 * AI-Ready Document Conversion Benchmark Leaderboard App
 */

let leaderboardData = [];
let localReviews = {}; // Keyed by agent_id
let localStars = {};   // Keyed by agent_id

// Load reviews and star ratings from localStorage if available
function initLocalStorage() {
  const savedRevs = localStorage.getItem("aiready_reviews");
  if (savedRevs) {
    try { localReviews = JSON.parse(savedRevs); } catch (e) {}
  }
  const savedStars = localStorage.getItem("aiready_stars");
  if (savedStars) {
    try { localStars = JSON.parse(savedStars); } catch (e) {}
  }
}

async function fetchLeaderboard() {
  initLocalStorage();
  try {
    const res = await fetch("data/leaderboard.json");
    const json = await res.json();
    leaderboardData = json.entries || [];
    document.getElementById("stat-total-agents").textContent = json.total_agents || leaderboardData.length;
    document.getElementById("last-updated").textContent = json.generated_at || "Just now";
    renderLeaderboard();
  } catch (err) {
    console.error("Failed to load leaderboard data", err);
    document.getElementById("leaderboard-tbody").innerHTML = `
      <tr><td colspan="9" style="text-align:center; padding: 2rem; color: #f87171;">
        Failed to load leaderboard data. Please make sure <code>docs/data/leaderboard.json</code> exists.
      </td></tr>`;
  }
}

function getSortedAndFilteredData() {
  const searchTerm = (document.getElementById("search-input").value || "").toLowerCase();
  const sortBy = document.getElementById("sort-select").value;

  let filtered = leaderboardData.filter(entry => {
    return (
      entry.agent_name.toLowerCase().includes(searchTerm) ||
      entry.author.toLowerCase().includes(searchTerm) ||
      (entry.tags && entry.tags.some(t => t.toLowerCase().includes(searchTerm)))
    );
  });

  filtered.sort((a, b) => {
    if (sortBy === "composite") return b.composite_score - a.composite_score;
    if (sortBy === "teds") return b.teds_score - a.teds_score;
    if (sortBy === "table") return b.table_score - a.table_score;
    if (sortBy === "image") return b.image_score - a.image_score;
    if (sortBy === "latency") return a.latency_ms - b.latency_ms; // Lower is better
    if (sortBy === "cost") return a.projected_cost_1k_gpt4o - b.projected_cost_1k_gpt4o; // Lower is better
    if (sortBy === "stars") {
      const aStars = getAgentStarAverage(a);
      const bStars = getAgentStarAverage(b);
      return bStars - aStars;
    }
    return 0;
  });

  return filtered;
}

function getAgentStarAverage(entry) {
  const allRevs = getAllReviewsForAgent(entry.agent_id, entry.reviews || []);
  if (allRevs.length === 0) return 0;
  const sum = allRevs.reduce((acc, r) => acc + r.rating, 0);
  return Number((sum / allRevs.length).toFixed(1));
}

function getAllReviewsForAgent(agentId, baseReviews) {
  const custom = localReviews[agentId] || [];
  return [...baseReviews, ...custom];
}

function renderLeaderboard() {
  const tbody = document.getElementById("leaderboard-tbody");
  const data = getSortedAndFilteredData();

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem; color: #9ca3af;">No tools match your query.</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map((entry, idx) => {
    const rankClass = idx === 0 ? "rank-1" : (idx === 1 ? "rank-2" : (idx === 2 ? "rank-3" : "rank-other"));
    const rankBadge = idx === 0 ? "🥇 1" : (idx === 1 ? "🥈 2" : (idx === 2 ? "🥉 3" : `#${idx + 1}`));
    const avgStars = getAgentStarAverage(entry);
    const starDisplay = avgStars > 0 ? `★ ${avgStars.toFixed(1)}` : `☆ New`;
    const revCount = getAllReviewsForAgent(entry.agent_id, entry.reviews || []).length;

    return `
      <tr>
        <td><span class="rank-badge ${rankClass}">${rankBadge}</span></td>
        <td>
          <div class="agent-title">
            ${entry.agent_name}
            <span style="font-size:0.75rem; color:#9ca3af;">v${entry.version}</span>
          </div>
          <div class="agent-meta">by ${entry.author} ${entry.repository_url ? `• <a href="${entry.repository_url}" target="_blank" style="color:#38bdf8;">repo</a>` : ""}</div>
        </td>
        <td><span class="score-pill">${entry.composite_score.toFixed(1)}</span></td>
        <td>${(entry.teds_score * 100).toFixed(1)}%</td>
        <td>${(entry.table_score * 100).toFixed(1)}%</td>
        <td>${(entry.image_score * 100).toFixed(1)}%</td>
        <td>${entry.latency_ms.toFixed(0)} ms</td>
        <td>$${entry.projected_cost_1k_gpt4o.toFixed(4)}</td>
        <td>
          <div class="star-rating-display">
            <span>${starDisplay}</span>
            <span style="font-size:0.75rem; color:#9ca3af;">(${revCount})</span>
          </div>
        </td>
        <td>
          <button class="btn btn-secondary" style="padding:0.35rem 0.75rem; font-size:0.8rem;" onclick="openDetailModal('${entry.agent_id}')">
            Details & Reviews
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

let activeAgentId = null;

function openDetailModal(agentId) {
  activeAgentId = agentId;
  const entry = leaderboardData.find(e => e.agent_id === agentId);
  if (!entry) return;

  document.getElementById("modal-agent-name").textContent = `${entry.agent_name} (v${entry.version})`;
  document.getElementById("modal-agent-desc").textContent = entry.description || "No description provided.";
  document.getElementById("modal-agent-author").textContent = `Author: ${entry.author} | OS: ${entry.system_env.os || 'Linux/Windows'}`;

  // Breakdown tables
  const breakdownTbody = document.getElementById("modal-breakdown-tbody");
  if (entry.case_breakdowns && entry.case_breakdowns.length > 0) {
    breakdownTbody.innerHTML = entry.case_breakdowns.map(c => `
      <tr>
        <td><strong>${c.case_name}</strong></td>
        <td><span class="badge-tag">${c.format}</span></td>
        <td><strong>${c.score.toFixed(1)}</strong></td>
        <td>${(c.teds * 100).toFixed(1)}%</td>
        <td>${(c.table * 100).toFixed(1)}%</td>
        <td>${(c.image * 100).toFixed(1)}%</td>
        <td>${c.latency.toFixed(0)} ms</td>
      </tr>
    `).join("");
  } else {
    breakdownTbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">Breakdown data not included.</td></tr>`;
  }

  // Render Reviews
  renderModalReviews(entry);

  // Setup Star Picker
  setupStarPicker(5);

  document.getElementById("modal-overlay").classList.add("active");
}

function closeDetailModal() {
  document.getElementById("modal-overlay").classList.remove("active");
  activeAgentId = null;
}

function setupStarPicker(initialRating = 5) {
  let selected = initialRating;
  const starsContainer = document.getElementById("star-picker-container");
  starsContainer.innerHTML = [1, 2, 3, 4, 5].map(n => `
    <span data-star="${n}" class="${n <= selected ? 'active' : ''}">★</span>
  `).join("");

  starsContainer.querySelectorAll("span").forEach(el => {
    el.addEventListener("click", () => {
      selected = parseInt(el.getAttribute("data-star"), 10);
      starsContainer.querySelectorAll("span").forEach(s => {
        const val = parseInt(s.getAttribute("data-star"), 10);
        s.classList.toggle("active", val <= selected);
      });
      starsContainer.setAttribute("data-current-rating", selected);
    });
  });
  starsContainer.setAttribute("data-current-rating", initialRating);
}

function renderModalReviews(entry) {
  const reviewsContainer = document.getElementById("modal-reviews-list");
  const allRevs = getAllReviewsForAgent(entry.agent_id, entry.reviews || []);

  if (allRevs.length === 0) {
    reviewsContainer.innerHTML = `<p style="color: #9ca3af; font-style: italic;">No community reviews yet. Be the first to leave one below!</p>`;
    return;
  }

  reviewsContainer.innerHTML = allRevs.map(r => `
    <div class="review-item">
      <div class="review-header">
        <div>
          <span class="review-author">${r.author}</span>
          <span class="review-persona">${r.persona}</span>
        </div>
        <div class="star-rating-display">
          ${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}
        </div>
      </div>
      <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem;">${r.title}</div>
      <p style="font-size: 0.9rem; color: #d1d5db;">${r.body}</p>
      <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;">${r.timestamp ? r.timestamp.split('T')[0] : ''}</div>
    </div>
  `).join("");
}

function handleAddReview(e) {
  e.preventDefault();
  if (!activeAgentId) return;

  const author = document.getElementById("review-author").value.trim() || "Anonymous Engineer";
  const persona = document.getElementById("review-persona").value;
  const title = document.getElementById("review-title").value.trim() || "Benchmark Feedback";
  const body = document.getElementById("review-body").value.trim();
  const rating = parseInt(document.getElementById("star-picker-container").getAttribute("data-current-rating") || "5", 10);

  if (!body) {
    alert("Please enter review feedback before submitting.");
    return;
  }

  const newReview = {
    review_id: "local-" + Date.now(),
    agent_id: activeAgentId,
    author: author,
    persona: persona,
    rating: rating,
    title: title,
    body: body,
    timestamp: new Date().toISOString(),
  };

  if (!localReviews[activeAgentId]) {
    localReviews[activeAgentId] = [];
  }
  localReviews[activeAgentId].unshift(newReview);
  localStorage.setItem("aiready_reviews", JSON.stringify(localReviews));

  // Reset form
  document.getElementById("review-title").value = "";
  document.getElementById("review-body").value = "";

  // Re-render
  const entry = leaderboardData.find(e => e.agent_id === activeAgentId);
  renderModalReviews(entry);
  renderLeaderboard();
  alert("Thank you! Your review and star rating have been recorded locally and reflected on the leaderboard.");
}

function openGitHubIssueTemplate() {
  if (!activeAgentId) return;
  const entry = leaderboardData.find(e => e.agent_id === activeAgentId);
  const title = encodeURIComponent(`[Review] Community Feedback for ${entry.agent_name}`);
  const body = encodeURIComponent(`### Agent Review: ${entry.agent_name} (v${entry.version})
- **Rating**: 5 / 5 stars
- **Persona**: [e.g. LLM/RAG Architect, MLOps, Enterprise Auditor]
- **Summary**:
[Your thoughts on table fidelity, image link integrity, and latency performance]
`);
  const url = `https://github.com/sun-flat-yamada/ai-ready-bench/issues/new?title=${title}&body=${body}`;
  window.open(url, "_blank");
}

document.addEventListener("DOMContentLoaded", () => {
  fetchLeaderboard();
  document.getElementById("search-input").addEventListener("input", renderLeaderboard);
  document.getElementById("sort-select").addEventListener("change", renderLeaderboard);
  document.getElementById("review-form").addEventListener("submit", handleAddReview);
  document.getElementById("modal-overlay").addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") closeDetailModal();
  });
});
