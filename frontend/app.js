const API = 'http://localhost:8000';
let currentJobId = null;
let pollInterval = null;

// ── Page Navigation ──────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`page-${name}`).classList.add('active');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const map = { home: 0, 'new-job': 1, jobs: 2 };
  if (map[name] !== undefined) document.querySelectorAll('.nav-btn')[map[name]].classList.add('active');
  if (name === 'jobs') loadJobs();
  window.scrollTo(0, 0);
}

// ── API Status ───────────────────────────────────────────────────
async function checkApi() {
  try {
    const res = await fetch(`${API}/`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      document.querySelector('.status-dot').className = 'status-dot online';
      document.querySelector('.nav-status span').textContent = 'API Online';
    }
  } catch {
    document.querySelector('.status-dot').className = 'status-dot offline';
    document.querySelector('.nav-status span').textContent = 'API Offline';
  }
}

// ── Submit Job ───────────────────────────────────────────────────
async function submitJob() {
  const title = document.getElementById('job-title').value.trim();
  const jdText = document.getElementById('jd-text').value.trim();
  const usernames = document.getElementById('github-users').value.trim();

  if (!title || !jdText || !usernames) {
    toast('Please fill in all fields', 'error');
    return;
  }

  const githubList = usernames.split(',').map(u => u.trim()).filter(Boolean);
  if (githubList.length === 0) {
    toast('Please enter at least one GitHub username', 'error');
    return;
  }
  if (githubList.length > 10) {
    toast('Maximum 10 candidates at once for the demo', 'error');
    return;
  }

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.textContent = '⚙️ Starting Pipeline...';

  try {
    const res = await fetch(`${API}/api/v1/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, jd_text: jdText, github_usernames: githubList })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();

    toast('Pipeline started! Redirecting...', 'success');
    currentJobId = data.job_id;
    openResults(data.job_id, title, githubList.length);

  } catch (err) {
    toast(`Error: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🚀 Start AI Analysis';
  }
}

// ── Results Page ─────────────────────────────────────────────────
function openResults(jobId, title, total) {
  currentJobId = jobId;
  document.getElementById('results-job-title').textContent = title || 'Analysis Results';
  document.getElementById('results-subtitle').textContent = `Analyzing ${total} candidate(s)...`;
  document.getElementById('progress-section').style.display = 'block';
  document.getElementById('candidates-section').style.display = 'none';
  showPage('results');
  startPolling(jobId, total);
}

function startPolling(jobId, total) {
  if (pollInterval) clearInterval(pollInterval);
  let elapsed = 0;

  pollInterval = setInterval(async () => {
    elapsed += 3;
    try {
      const res = await fetch(`${API}/api/v1/jobs/${jobId}/status`);
      const data = await res.json();

      document.getElementById('progress-msg').textContent = data.message || 'Processing...';
      const pct = total > 0 ? Math.round((data.progress || 0) / total * 100) : Math.min(elapsed * 2, 90);
      document.getElementById('progress-bar').style.width = `${pct}%`;

      if (data.status === 'completed') {
        clearInterval(pollInterval);
        document.getElementById('progress-bar').style.width = '100%';
        setTimeout(() => loadResults(jobId), 500);
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        document.getElementById('progress-msg').textContent = `Error: ${data.message}`;
        toast('Pipeline error. Check console.', 'error');
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  }, 3000);
}

async function loadResults(jobId) {
  try {
    const res = await fetch(`${API}/api/v1/jobs/${jobId}/candidates`);
    const data = await res.json();

    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('candidates-section').style.display = 'block';
    document.getElementById('results-subtitle').textContent =
      `${data.candidates.length} candidates ranked by evidence-based AI score`;

    const list = document.getElementById('candidates-list');
    if (data.candidates.length === 0) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">🤷</div><p>No candidates found. Check usernames.</p></div>`;
      return;
    }
    list.innerHTML = data.candidates.map(c => renderCandidateCard(c)).join('');
  } catch (err) {
    toast('Error loading results', 'error');
    console.error(err);
  }
}

function renderCandidateCard(c) {
  const rankClass = c.rank === 1 ? 'gold' : c.rank === 2 ? 'silver' : c.rank === 3 ? 'bronze' : '';
  const rankEmoji = c.rank === 1 ? '🥇' : c.rank === 2 ? '🥈' : c.rank === 3 ? '🥉' : `#${c.rank}`;
  const langs = Object.keys(c.languages || {}).slice(0, 5);
  const scoreColor = c.total_score >= 70 ? '#10b981' : c.total_score >= 50 ? '#f59e0b' : '#ef4444';

  return `
    <div class="candidate-card rank-${c.rank}" onclick="openCandidate('${c.id}', '${currentJobId}')">
      <div class="cand-top">
        <div class="cand-rank ${rankClass}">${rankEmoji}</div>
        <img class="cand-avatar" src="${c.avatar_url || 'https://github.com/identicons/' + c.github_username + '.png'}" alt="${c.name}" onerror="this.src='https://github.com/identicons/${c.github_username}.png'" />
        <div class="cand-info">
          <div class="cand-name">${c.name || c.github_username}</div>
          <div class="cand-handle">@${c.github_username} · ${c.public_repos} repos · ${c.followers} followers</div>
          <div class="cand-location">${c.location || 'Location unknown'}</div>
        </div>
        <span class="cand-fraud ${c.fraud_risk}">${c.fraud_risk} Risk</span>
        <div class="cand-score-main">
          <div class="score-big" style="color:${scoreColor}">${c.total_score.toFixed(1)}</div>
          <div class="score-label">/ 100</div>
        </div>
      </div>

      <div class="score-bars">
        <div class="score-bar-item">
          <div class="score-bar-label">Technical</div>
          <div class="score-bar-track"><div class="score-bar-fill tech" style="width:${c.technical_score}%"></div></div>
          <div class="score-bar-val">${c.technical_score.toFixed(0)}</div>
        </div>
        <div class="score-bar-item">
          <div class="score-bar-label">Quality</div>
          <div class="score-bar-track"><div class="score-bar-fill qual" style="width:${c.code_quality_score}%"></div></div>
          <div class="score-bar-val">${c.code_quality_score.toFixed(0)}</div>
        </div>
        <div class="score-bar-item">
          <div class="score-bar-label">Velocity</div>
          <div class="score-bar-track"><div class="score-bar-fill vel" style="width:${c.learning_velocity_score}%"></div></div>
          <div class="score-bar-val">${c.learning_velocity_score.toFixed(0)}</div>
        </div>
        <div class="score-bar-item">
          <div class="score-bar-label">Collab</div>
          <div class="score-bar-track"><div class="score-bar-fill col" style="width:${c.collaboration_score}%"></div></div>
          <div class="score-bar-val">${c.collaboration_score.toFixed(0)}</div>
        </div>
        <div class="score-bar-item">
          <div class="score-bar-label">Alignment</div>
          <div class="score-bar-track"><div class="score-bar-fill align" style="width:${c.skill_alignment_score}%"></div></div>
          <div class="score-bar-val">${c.skill_alignment_score.toFixed(0)}</div>
        </div>
      </div>

      <div class="cand-langs">
        ${langs.map(l => `<span class="lang-tag">${l}</span>`).join('')}
        <span style="font-size:12px;color:var(--text-dim);align-self:center">Confidence: ${(c.confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  `;
}

// ── Candidate Detail ─────────────────────────────────────────────
async function openCandidate(candidateId, jobId) {
  try {
    const res = await fetch(`${API}/api/v1/jobs/${jobId}/candidates`);
    const data = await res.json();
    const c = data.candidates.find(x => x.id === candidateId);
    if (!c) return;

    const detail = document.getElementById('candidate-detail');
    const scoreColor = c.total_score >= 70 ? '#10b981' : c.total_score >= 50 ? '#f59e0b' : '#ef4444';
    const pct = Math.round(c.total_score * 3.6);

    detail.innerHTML = `
      <div class="detail-hero">
        <img class="detail-avatar" src="${c.avatar_url}" alt="${c.name}" />
        <div class="detail-info">
          <div class="detail-name">${c.name || c.github_username}</div>
          <div class="detail-handle">
            <a href="https://github.com/${c.github_username}" target="_blank" style="color:var(--accent);text-decoration:none">
              github.com/${c.github_username} ↗
            </a>
          </div>
          <div class="detail-bio">${c.bio || 'No bio provided.'}</div>
          <div class="detail-meta">
            <span class="detail-meta-item">📦 <strong>${c.public_repos}</strong> repos</span>
            <span class="detail-meta-item">👥 <strong>${c.followers}</strong> followers</span>
            <span class="detail-meta-item">📍 ${c.location || 'Unknown'}</span>
            <span class="cand-fraud ${c.fraud_risk}" style="font-size:12px;padding:4px 10px">${c.fraud_risk} Fraud Risk (${(c.fraud_score * 100).toFixed(0)}%)</span>
          </div>
        </div>
        <div class="detail-score-hero">
          <div class="score-circle" style="--pct:${pct}deg">
            <div class="score-circle-inner">
              <span class="score-circle-num" style="color:${scoreColor}">${c.total_score.toFixed(1)}</span>
              <span class="score-circle-lbl">/ 100</span>
            </div>
          </div>
          <div style="font-size:12px;color:var(--text-muted);text-align:center">Confidence: ${(c.confidence*100).toFixed(0)}%</div>
          <div style="font-size:12px;color:var(--text-muted);text-align:center">Rank #${c.rank}</div>
        </div>
      </div>

      <div class="detail-grid">
        <!-- XAI Explanation -->
        <div class="detail-card" style="grid-column:1/-1">
          <div class="detail-card-title">🔍 AI Explanation</div>
          <div class="xai-text">${(c.explanation || 'No explanation generated.').replace(/\n/g, '<br>')}</div>
        </div>

        <!-- Score Breakdown -->
        <div class="detail-card">
          <div class="detail-card-title">📊 Score Breakdown</div>
          ${[
            ['⚙️ Technical Execution', c.technical_score, 'tech'],
            ['✨ Code Quality', c.code_quality_score, 'qual'],
            ['🚀 Learning Velocity', c.learning_velocity_score, 'vel'],
            ['🤝 Collaboration', c.collaboration_score, 'col'],
            ['🎯 Skill Alignment', c.skill_alignment_score, 'align'],
          ].map(([label, score, cls]) => `
            <div style="margin-bottom:12px">
              <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px">
                <span>${label}</span><strong>${score.toFixed(1)}</strong>
              </div>
              <div class="score-bar-track" style="height:8px">
                <div class="score-bar-fill ${cls}" style="width:${score}%"></div>
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Skill Proofs -->
        <div class="detail-card">
          <div class="detail-card-title">✅ Skill Proofs</div>
          ${(c.skill_proofs || []).length ? c.skill_proofs.map(p => `
            <div class="proof-item">
              <span class="proof-icon">🔗</span>
              <div>
                <span class="proof-skill">${p.skill}</span>
                <div class="proof-text">${p.proof}</div>
              </div>
              <span class="conf-badge">${(p.confidence * 100).toFixed(0)}%</span>
            </div>
          `).join('') : '<p style="color:var(--text-muted);font-size:13px">No proofs generated.</p>'}

          ${(c.skill_gaps || []).length ? `
            <div class="detail-card-title" style="margin-top:20px">⚠️ Skill Gaps</div>
            <div>${c.skill_gaps.map(g => `<span class="gap-tag">⛔ ${g}</span>`).join('')}</div>
          ` : ''}
        </div>

        <!-- Top Repositories -->
        <div class="detail-card">
          <div class="detail-card-title">📁 Top Repositories</div>
          ${(c.top_repos || []).map(r => `
            <div class="repo-item">
              <a class="repo-name" href="${r.url}" target="_blank">${r.name} ↗</a>
              <div class="repo-desc">${r.description || 'No description'}</div>
              <div class="repo-meta">
                <span class="repo-meta-item">💬 <strong>${r.language || '?'}</strong></span>
                <span class="repo-meta-item">📝 <strong>${r.commits}</strong> commits</span>
                <span class="repo-meta-item">⭐ <strong>${r.stars}</strong></span>
                <span class="repo-meta-item">📖 README: <strong>${r.has_readme ? '✅' : '❌'}</strong></span>
                <span class="repo-meta-item">🧪 Tests: <strong>${r.has_tests ? '✅' : '❌'}</strong></span>
              </div>
            </div>
          `).join('') || '<p style="color:var(--text-muted);font-size:13px">No repositories found.</p>'}
        </div>

        <!-- Fraud Analysis -->
        <div class="detail-card">
          <div class="detail-card-title">🛡️ Fraud Analysis</div>
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
            <span class="cand-fraud ${c.fraud_risk}" style="font-size:14px;padding:6px 16px">${c.fraud_risk} Risk</span>
            <span style="font-size:22px;font-weight:900;color:var(--text)">${(c.fraud_score * 100).toFixed(0)}%</span>
            <span style="font-size:13px;color:var(--text-muted)">fraud score</span>
          </div>
          ${(c.fraud_signals || []).length ? `
            <div class="fraud-signals">
              ${c.fraud_signals.map(s => `
                <div class="fraud-signal">
                  <div class="fraud-signal-dot"></div>
                  <span>${s}</span>
                </div>
              `).join('')}
            </div>
          ` : '<p style="color:var(--green);font-size:13px">✅ No fraud signals detected</p>'}
        </div>

        <!-- Interview Questions -->
        <div class="detail-card" style="grid-column:1/-1">
          <div class="detail-card-title">🎯 Personalized Interview Questions</div>
          ${(c.interview_questions || []).map((q, i) => `
            <div class="q-item">
              <div class="q-type ${q.type || 'technical'}">${(q.type || 'technical').replace('_', ' ').toUpperCase()}</div>
              <div class="q-text">Q${i+1}. ${q.question}</div>
              ${q.follow_up ? `<div class="q-followup">↳ Follow-up: ${q.follow_up}</div>` : ''}
            </div>
          `).join('') || '<p style="color:var(--text-muted);font-size:13px">No questions generated.</p>'}
        </div>
      </div>
    `;

    showPage('candidate');
  } catch (err) {
    toast('Error loading candidate detail', 'error');
    console.error(err);
  }
}

function goBackToResults() {
  showPage('results');
  if (currentJobId) {
    // Re-check if still processing
    fetch(`${API}/api/v1/jobs/${currentJobId}/status`)
      .then(r => r.json())
      .then(d => {
        if (d.status === 'completed') {
          document.getElementById('progress-section').style.display = 'none';
          document.getElementById('candidates-section').style.display = 'block';
        }
      }).catch(() => {});
  }
}

// ── Load All Jobs ────────────────────────────────────────────────
async function loadJobs() {
  const list = document.getElementById('jobs-list');
  list.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted)">Loading...</div>';
  try {
    const res = await fetch(`${API}/api/v1/jobs`);
    const jobs = await res.json();

    if (!jobs.length) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><p>No jobs yet. <a href="#" onclick="showPage('new-job')">Create your first job →</a></p></div>`;
      return;
    }

    list.innerHTML = jobs.map(j => `
      <div class="job-item" onclick="openJobResults('${j.id}', '${escapeHtml(j.title)}')">
        <div class="job-item-icon">💼</div>
        <div class="job-item-info">
          <div class="job-item-title">${j.title}</div>
          <div class="job-item-meta">
            ${j.seniority ? j.seniority + ' • ' : ''}
            ${(j.skills || []).slice(0, 4).join(', ') || 'No skills extracted'}
            <br>Created ${new Date(j.created_at + 'Z').toLocaleString()}
          </div>
        </div>
        <span class="job-item-status ${j.status}">${j.status}</span>
      </div>
    `).join('');
  } catch (err) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Cannot connect to API. Is the backend running?</p></div>`;
  }
}

async function openJobResults(jobId, title) {
  currentJobId = jobId;
  document.getElementById('results-job-title').textContent = title;
  document.getElementById('progress-section').style.display = 'none';
  document.getElementById('candidates-section').style.display = 'none';
  showPage('results');

  try {
    const statusRes = await fetch(`${API}/api/v1/jobs/${jobId}/status`);
    const status = await statusRes.json();

    if (status.status === 'processing') {
      document.getElementById('progress-section').style.display = 'block';
      document.getElementById('results-subtitle').textContent = status.message;
      startPolling(jobId, status.total || 5);
    } else {
      await loadResults(jobId);
    }
  } catch {
    await loadResults(jobId);
  }
}

// ── Toast ────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

function escapeHtml(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ── Init ─────────────────────────────────────────────────────────
checkApi();
setInterval(checkApi, 10000);
