// AI YouTube to Shorts & Reels Studio Frontend Logic

let currentInputMode = 'youtube';
let uploadedFilePath = null;
let currentJobId = null;
let currentReelsData = [];
let activeReelIndex = 0;
let progressPollInterval = null;

// Tab Switching
function switchInputTab(mode) {
    currentInputMode = mode;
    const tabYt = document.getElementById('tab-youtube');
    const tabUp = document.getElementById('tab-upload');
    const contentYt = document.getElementById('youtube-content');
    const contentUp = document.getElementById('upload-content');

    if (mode === 'youtube') {
        tabYt.classList.add('active');
        tabUp.classList.remove('active');
        contentYt.classList.remove('hidden');
        contentUp.classList.add('hidden');
    } else {
        tabUp.classList.add('active');
        tabYt.classList.remove('active');
        contentUp.classList.remove('hidden');
        contentYt.classList.add('hidden');
    }
    lucide.createIcons();
}

// Clipboard Paste
async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            document.getElementById('video-url-input').value = text;
        }
    } catch (err) {
        console.warn('Could not read clipboard:', err);
    }
}

// Sample Selection
function loadSample(url, title) {
    switchInputTab('youtube');
    document.getElementById('video-url-input').value = url;
}

// File Drag & Drop
const dropZone = document.getElementById('drop-zone');
if (dropZone) {
    dropZone.addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleUploadedFile(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(event) {
    if (event.target.files.length > 0) {
        handleUploadedFile(event.target.files[0]);
    }
}

async function handleUploadedFile(file) {
    const infoBadge = document.getElementById('selected-file-info');
    const fileNameSpan = document.getElementById('selected-file-name');
    fileNameSpan.textContent = `Uploading ${file.name}...`;
    infoBadge.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            uploadedFilePath = data.file_path;
            fileNameSpan.textContent = `Ready: ${file.name} (${Math.round(data.duration || 0)}s)`;
        } else {
            fileNameSpan.textContent = `Upload failed: ${data.detail || 'Error'}`;
        }
    } catch (err) {
        fileNameSpan.textContent = `Upload failed: ${err.message}`;
    }
}

let currentStudioMode = 'transformative_hindi';

// Mode Switching (Transformative Hindi vs Direct Highlights)
function setStudioMode(mode) {
    currentStudioMode = mode;
    const btnTrans = document.getElementById('mode-transformative');
    const btnDirect = document.getElementById('mode-direct');
    const voiceItem = document.getElementById('item-voice-selector');
    const styleItem = document.getElementById('item-story-style');

    if (mode === 'transformative_hindi') {
        btnTrans.classList.add('active');
        btnDirect.classList.remove('active');
        voiceItem?.classList.remove('hidden');
        styleItem?.classList.remove('hidden');
    } else {
        btnDirect.classList.add('active');
        btnTrans.classList.remove('active');
        voiceItem?.classList.add('hidden');
        styleItem?.classList.add('hidden');
    }
    lucide.createIcons();
}

// Generation Trigger
async function startGeneration() {
    const btn = document.getElementById('btn-start-generate');
    const url = document.getElementById('video-url-input').value.trim();
    const numReels = parseInt(document.getElementById('config-num-reels').value, 10);
    const theme = document.getElementById('config-theme').value;
    const position = document.getElementById('config-position')?.value || 'bottom';
    const analysisRangeVal = parseFloat(document.getElementById('config-analysis-range')?.value || 0);
    const voiceId = document.getElementById('config-voice')?.value || 'hi-IN-MadhurNeural';
    const storyStyle = document.getElementById('config-story-style')?.value || 'viral_mystery';
    const audioVibe = document.getElementById('config-audio-vibe')?.value || 'mystery_suspense';

    if (currentInputMode === 'youtube' && !url) {
        alert('Please enter a valid YouTube video URL or select a demo sample.');
        return;
    }

    if (currentInputMode === 'upload' && !uploadedFilePath) {
        alert('Please upload a video file first.');
        return;
    }

    // Disable button & Show Progress Section
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-content"><i data-lucide="loader-2" class="spin"></i> Starting AI Engine...</span>`;
    lucide.createIcons();

    document.getElementById('progress-section').classList.remove('hidden');
    document.getElementById('studio-section').classList.add('hidden');
    window.location.hash = 'progress-section';

    const payload = {
        mode: currentStudioMode,
        num_reels: numReels,
        caption_theme: theme,
        caption_position: position,
        voice_id: voiceId,
        story_style: storyStyle,
        audio_vibe: audioVibe,
        max_analysis_duration: analysisRangeVal > 0 ? analysisRangeVal : null,
        layout_mode: 'blur_canvas',
        enable_emojis: true
    };

    if (currentInputMode === 'youtube') {
        payload.url = url;
    } else {
        payload.file_path = uploadedFilePath;
    }

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.job_id) {
            currentJobId = data.job_id;
            startPollingProgress(currentJobId);
        } else {
            throw new Error(data.detail || 'Failed to start generation');
        }
    } catch (err) {
        alert(`Error: ${err.message}`);
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-content"><i data-lucide="sparkles"></i> Generate Viral Reels with Captions</span>`;
        lucide.createIcons();
    }
}

// Progress Poller
function startPollingProgress(jobId) {
    if (progressPollInterval) clearInterval(progressPollInterval);

    progressPollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/progress/${jobId}`);
            if (!res.ok) return;

            const data = await res.json();
            updateProgressUI(data);

            if (data.status === 'completed') {
                clearInterval(progressPollInterval);
                onGenerationComplete(data);
            } else if (data.status === 'failed') {
                clearInterval(progressPollInterval);
                alert(`Generation failed: ${data.error || data.message}`);
                resetGenerateBtn();
            }
        } catch (err) {
            console.warn('Progress poll error:', err);
        }
    }, 1200);
}

function updateProgressUI(data) {
    const percent = Math.round(data.percent || 0);
    document.getElementById('progress-percent').textContent = `${percent}%`;
    document.getElementById('progress-bar-fill').style.width = `${percent}%`;
    document.getElementById('progress-title').textContent = data.message || 'Processing video...';
    document.getElementById('progress-detail-msg').textContent = data.message || '';

    // Step indicators
    const stepDl = document.getElementById('step-dl');
    const stepAi = document.getElementById('step-ai');
    const stepHook = document.getElementById('step-hook');
    const stepRender = document.getElementById('step-render');

    [stepDl, stepAi, stepHook, stepRender].forEach(s => s.className = 'step-item');

    if (data.stage === 'downloading') {
        stepDl.classList.add('active');
    } else if (data.stage === 'transcribing') {
        stepDl.classList.add('completed');
        stepAi.classList.add('active');
    } else if (data.stage === 'analyzing') {
        stepDl.classList.add('completed');
        stepAi.classList.add('completed');
        stepHook.classList.add('active');
    } else if (data.stage === 'rendering') {
        stepDl.classList.add('completed');
        stepAi.classList.add('completed');
        stepHook.classList.add('completed');
        stepRender.classList.add('active');
    } else if (data.status === 'completed') {
        stepDl.classList.add('completed');
        stepAi.classList.add('completed');
        stepHook.classList.add('completed');
        stepRender.classList.add('completed');
    }
}

function onGenerationComplete(data) {
    resetGenerateBtn();
    currentReelsData = data.reels || [];

    if (currentReelsData.length === 0) {
        alert('No reels could be rendered.');
        return;
    }

    renderReelsGrid(currentReelsData);
    selectReel(0);

    // Show Studio Section
    document.getElementById('progress-section').classList.add('hidden');
    document.getElementById('studio-section').classList.remove('hidden');
    window.location.hash = 'studio-section';
    lucide.createIcons();

    // Refresh history badge
    updateHistoryBadge();
}

function resetGenerateBtn() {
    const btn = document.getElementById('btn-start-generate');
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-content"><i data-lucide="sparkles"></i> Generate Viral Reels with Captions</span>`;
    lucide.createIcons();
}

// Render Reels List
function renderReelsGrid(reels) {
    const container = document.getElementById('reels-container');
    container.innerHTML = '';

    reels.forEach((reel, index) => {
        const card = document.createElement('div');
        card.className = `reel-card ${index === activeReelIndex ? 'active' : ''}`;
        card.onclick = () => selectReel(index);

        card.innerHTML = `
            <div class="reel-card-thumb">
                <span class="reel-number">#${index + 1}</span>
                <div class="virality-tag">🔥 ${reel.virality_score || 95}</div>
            </div>
            <div class="reel-card-content">
                <h5 class="reel-card-title">${reel.title}</h5>
                <p class="reel-card-hook">"${reel.hook || ''}"</p>
                <div class="reel-card-meta">
                    <span><i data-lucide="clock"></i> ${Math.round(reel.duration || 0)}s</span>
                    <span><i data-lucide="sparkles"></i> 9:16</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    lucide.createIcons();
}

let currentSocialPlatform = 'instagram';

// Select Reel to preview & edit
function selectReel(index) {
    if (index < 0 || index >= currentReelsData.length) return;
    activeReelIndex = index;
    const reel = currentReelsData[index];

    // Highlight active card
    const cards = document.querySelectorAll('.reel-card');
    cards.forEach((c, idx) => {
        if (idx === index) c.classList.add('active');
        else c.classList.remove('active');
    });

    // Update Player & Header
    const video = document.getElementById('main-reel-video');
    video.src = reel.video_url;
    video.load();

    document.getElementById('active-clip-title').textContent = reel.title;
    document.getElementById('active-virality-chip').textContent = `🔥 ${reel.virality_score || 95}/100 Viral Score`;
    document.getElementById('btn-direct-download').href = reel.download_url;

    // Populate live trimmer inputs
    document.getElementById('edit-start-time').value = reel.start_time || 0;
    document.getElementById('edit-end-time').value = reel.end_time || reel.duration || 30;
    if (reel.caption_theme) document.getElementById('edit-theme').value = reel.caption_theme;
    if (reel.layout_mode) document.getElementById('edit-layout').value = reel.layout_mode;
    if (reel.caption_position) document.getElementById('edit-position').value = reel.caption_position;

    // Reset publish toast
    const toast = document.getElementById('publish-result-toast');
    if (toast) toast.classList.add('hidden');

    // Update Social Posting Dashboard
    updateSocialPreview(reel);
    lucide.createIcons();
}

// Switch Active Social Platform (Instagram / YouTube / Facebook)
function switchSocialPlatform(platform) {
    currentSocialPlatform = platform;
    const tabIg = document.getElementById('plat-tab-ig');
    const tabYt = document.getElementById('plat-tab-yt');
    const tabFb = document.getElementById('plat-tab-fb');

    [tabIg, tabYt, tabFb].forEach(t => t?.classList.remove('active'));
    if (platform === 'instagram') tabIg?.classList.add('active');
    else if (platform === 'youtube') tabYt?.classList.add('active');
    else if (platform === 'facebook') tabFb?.classList.add('active');

    const reel = currentReelsData[activeReelIndex];
    if (reel) updateSocialPreview(reel);
    lucide.createIcons();
}

function updateSocialPreview(reel) {
    const sp = reel.social_pack || {};
    const tipElem = document.getElementById('platform-tip-text');
    const previewElem = document.getElementById('social-text-preview');
    const labelElem = document.getElementById('copy-btn-platform-label');

    if (currentSocialPlatform === 'instagram') {
        const ig = sp.instagram || {};
        labelElem.textContent = 'Instagram';
        tipElem.textContent = ig.audio_tip ? `🎵 ${ig.audio_tip} (Best Post Time: ${ig.best_time_to_post})` : 'Add trending audio track at 5% volume for optimal algorithm push.';
        previewElem.textContent = ig.caption || `${reel.title}\n\n${reel.hook || ''}\n\n${(reel.hashtags || []).join(' ')}`;
    } else if (currentSocialPlatform === 'youtube') {
        const yt = sp.youtube || {};
        labelElem.textContent = 'YouTube Shorts';
        tipElem.textContent = yt.shorts_hashtag_tip || 'Keep title under 60 characters with #Shorts for maximum mobile feed CTR.';
        
        const tagsStr = (yt.tags || reel.hashtags || []).join(', ');
        previewElem.textContent = `TITLE:\n${yt.title || reel.title + ' #Shorts'}\n\nPINNED COMMENT:\n${yt.pinned_comment || 'What was your favorite moment in this clip? Drop a comment below!'}\n\nDESCRIPTION:\n${yt.description || reel.title}\n\nTAGS:\n${tagsStr}`;
    } else if (currentSocialPlatform === 'facebook') {
        const fb = sp.facebook || {};
        labelElem.textContent = 'Facebook Reels';
        tipElem.textContent = fb.engagement_question ? `💬 Question: "${fb.engagement_question}"` : 'Prompt discussions in the caption to trigger Facebook Reels comment velocity.';
        previewElem.textContent = fb.caption || `🔥 ${reel.title}\n\n${reel.hook || ''}\n\n${(reel.hashtags || []).join(' ')}`;
    }
}

// Copy Active Social Post
function copyActiveSocialPost() {
    const text = document.getElementById('social-text-preview').textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('.btn-copy-full');
        const oldHtml = btn.innerHTML;
        btn.innerHTML = `<i data-lucide="check"></i> Copied to Clipboard!`;
        lucide.createIcons();
        setTimeout(() => {
            btn.innerHTML = oldHtml;
            lucide.createIcons();
        }, 2500);
    });
}

// Live Re-Render Active Reel
async function reRenderActiveClip() {
    const reel = currentReelsData[activeReelIndex];
    if (!reel || !currentJobId) return;

    const btn = document.getElementById('btn-rerender-clip');
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Rendering...`;
    lucide.createIcons();

    const startTime = parseFloat(document.getElementById('edit-start-time').value);
    const endTime = parseFloat(document.getElementById('edit-end-time').value);
    const theme = document.getElementById('edit-theme').value;
    const color = document.getElementById('edit-color').value;
    const layout = document.getElementById('edit-layout').value;
    const position = document.getElementById('edit-position').value;

    const payload = {
        job_id: currentJobId,
        clip_id: reel.id,
        start_time: startTime,
        end_time: endTime,
        layout_mode: layout,
        caption_theme: theme,
        highlight_color: color,
        caption_position: position,
        enable_emojis: true
    };

    try {
        const res = await fetch('/api/re-render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            currentReelsData[activeReelIndex] = data.clip;
            renderReelsGrid(currentReelsData);
            selectReel(activeReelIndex);
        } else {
            alert(`Re-render failed: ${data.detail || 'Error'}`);
        }
    } catch (err) {
        alert(`Re-render error: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="refresh-cw"></i> Re-Render Clip`;
        lucide.createIcons();
    }
}

// Download All ZIP
function downloadAllZip() {
    if (!currentJobId) return;
    window.location.href = `/api/download-all/${currentJobId}`;
}

// Reset Studio
function resetStudio() {
    document.getElementById('studio-section').classList.add('hidden');
    document.getElementById('progress-section').classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================
// 📜 PROCESSED VIDEO HISTORY MODULE
// ==========================================

async function openHistoryDrawer() {
    const drawer = document.getElementById('history-drawer');
    const overlay = document.getElementById('history-overlay');
    drawer.classList.remove('hidden');
    overlay.classList.remove('hidden');

    const container = document.getElementById('history-list-container');
    container.innerHTML = `<div class="history-empty"><i data-lucide="loader-2" class="spin"></i><p>Loading your history...</p></div>`;
    lucide.createIcons();

    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const items = data.history || [];

        if (items.length === 0) {
            container.innerHTML = `
                <div class="history-empty">
                    <i data-lucide="film"></i>
                    <p>No processed videos yet. Generate your first reel to see it here!</p>
                </div>`;
        } else {
            container.innerHTML = '';
            items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'history-card';
                const thumb = item.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&auto=format&fit=crop&q=60';
                
                card.innerHTML = `
                    <img src="${thumb}" class="history-thumb" alt="Thumbnail" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&auto=format&fit=crop&q=60'">
                    <div class="history-card-info" onclick="loadHistoryJob('${item.job_id}')">
                        <div class="history-card-title">${item.title}</div>
                        <div class="history-card-meta">
                            <span>📅 ${item.created_at || 'Recently'}</span>
                            <span>⏱️ ${Math.round(item.duration || 0)}s</span>
                        </div>
                        <span class="history-reels-count">🎬 ${item.reels_count} Reels Generated</span>
                    </div>
                    <button class="history-card-del" title="Delete from history" onclick="deleteHistoryJob(event, '${item.job_id}')">
                        <i data-lucide="trash-2"></i>
                    </button>
                `;
                container.appendChild(card);
            });
        }
    } catch (err) {
        container.innerHTML = `<div class="history-empty"><p>Error loading history: ${err.message}</p></div>`;
    }
    lucide.createIcons();
}

function closeHistoryDrawer() {
    document.getElementById('history-drawer').classList.add('hidden');
    document.getElementById('history-overlay').classList.add('hidden');
}

async function loadHistoryJob(jobId) {
    closeHistoryDrawer();
    try {
        const res = await fetch(`/api/history/${jobId}`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            const job = data.job;
            currentJobId = job.job_id;
            currentReelsData = job.reels || [];

            if (currentReelsData.length > 0) {
                renderReelsGrid(currentReelsData);
                selectReel(0);
                document.getElementById('progress-section').classList.add('hidden');
                document.getElementById('studio-section').classList.remove('hidden');
                window.location.hash = 'studio-section';
            } else {
                alert('No reels found for this history item.');
            }
        } else {
            alert(`Could not load job: ${data.detail || 'Error'}`);
        }
    } catch (err) {
        alert(`Failed to load history job: ${err.message}`);
    }
}

async function deleteHistoryJob(event, jobId) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this video from history?')) return;

    try {
        const res = await fetch(`/api/history/${jobId}`, { method: 'DELETE' });
        if (res.ok) {
            openHistoryDrawer();
            updateHistoryBadge();
        }
    } catch (err) {
        alert(`Delete failed: ${err.message}`);
    }
}

async function updateHistoryBadge() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const count = (data.history || []).length;
        const badge = document.getElementById('history-badge');
        if (badge) badge.textContent = count;
    } catch (err) {
        console.warn('Could not update history badge:', err);
    }
}

// ==========================================
// 🚀 SOCIAL ACCOUNTS & 1-CLICK PUBLISHING
// ==========================================

async function openSocialModal() {
    const modal = document.getElementById('social-modal');
    const overlay = document.getElementById('social-modal-overlay');
    modal.classList.remove('hidden');
    overlay.classList.remove('hidden');

    try {
        const res = await fetch('/api/social/accounts');
        const data = await res.json();
        const accs = data.accounts || {};

        // Update badges & populate fields if available
        for (const [plat, conf] of Object.entries(accs)) {
            const badge = document.getElementById(`badge-status-${plat}`);
            if (badge) {
                if (conf.connected) {
                    badge.textContent = `🟢 Connected (${conf.account_name || 'Active'})`;
                    badge.classList.add('connected');
                } else {
                    badge.textContent = `⚪ Not Connected`;
                    badge.classList.remove('connected');
                }
            }
            if (plat === 'webhook' && conf.webhook_url) {
                const inp = document.getElementById('acc-webhook-url');
                if (inp) inp.value = conf.webhook_url;
            }
        }
    } catch (err) {
        console.warn('Error loading social accounts:', err);
    }
    lucide.createIcons();
}

function closeSocialModal() {
    document.getElementById('social-modal').classList.add('hidden');
    document.getElementById('social-modal-overlay').classList.add('hidden');
}

async function saveSocialAccount(platform) {
    let creds = {};
    if (platform === 'instagram') {
        creds.ig_user_id = document.getElementById('acc-ig-user-id')?.value.trim();
        creds.access_token = document.getElementById('acc-ig-token')?.value.trim();
    } else if (platform === 'youtube') {
        creds.access_token = document.getElementById('acc-yt-token')?.value.trim();
    } else if (platform === 'twitter') {
        creds.bearer_token = document.getElementById('acc-tw-token')?.value.trim();
    } else if (platform === 'webhook') {
        creds.webhook_url = document.getElementById('acc-webhook-url')?.value.trim();
    }

    try {
        const res = await fetch('/api/social/accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform, credentials: creds })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ ${platform.toUpperCase()} account settings saved successfully!`);
            openSocialModal();
            updateSocialNavStatus();
        } else {
            alert(`Save failed: ${data.detail || 'Error'}`);
        }
    } catch (err) {
        alert(`Error saving credentials: ${err.message}`);
    }
}

async function disconnectSocialAccount(platform) {
    try {
        const res = await fetch('/api/social/disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform })
        });
        if (res.ok) {
            openSocialModal();
            updateSocialNavStatus();
        }
    } catch (err) {
        alert(`Disconnect failed: ${err.message}`);
    }
}

async function updateSocialNavStatus() {
    try {
        const res = await fetch('/api/social/accounts');
        const data = await res.json();
        const accs = data.accounts || {};
        const anyConnected = Object.values(accs).some(a => a.connected);
        const dot = document.getElementById('nav-social-dot');
        if (dot) {
            dot.style.background = anyConnected ? '#10b981' : '#6b7280';
            dot.style.boxShadow = anyConnected ? '0 0 6px #10b981' : 'none';
        }
    } catch (err) {
        console.warn('Could not update social nav status:', err);
    }
}

// 1-Click Multi-Platform Reel Publishing
async function publishActiveReelToSocial() {
    const reel = currentReelsData[activeReelIndex];
    if (!reel) {
        alert('Please select a reel first.');
        return;
    }

    const selectedPlatforms = [];
    if (document.getElementById('pub-check-ig')?.checked) selectedPlatforms.push('instagram');
    if (document.getElementById('pub-check-yt')?.checked) selectedPlatforms.push('youtube');
    if (document.getElementById('pub-check-tw')?.checked) selectedPlatforms.push('twitter');
    if (document.getElementById('pub-check-tt')?.checked) selectedPlatforms.push('tiktok');
    if (document.getElementById('pub-check-hook')?.checked) selectedPlatforms.push('webhook');

    if (selectedPlatforms.length === 0) {
        alert('Please select at least one social media platform checkbox.');
        return;
    }

    const btn = document.getElementById('btn-publish-now');
    const toast = document.getElementById('publish-result-toast');
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-content"><i data-lucide="loader-2" class="spin"></i> Publishing to ${selectedPlatforms.length} Platform(s)...</span>`;
    lucide.createIcons();

    toast.classList.remove('hidden');
    toast.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Uploading video and syndicating to social feeds...`;
    lucide.createIcons();

    try {
        const res = await fetch('/api/social/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platforms: selectedPlatforms,
                reel: reel,
                host_url: window.location.origin
            })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            const results = data.results || {};
            let htmlMsg = `<div style="font-weight:700; margin-bottom:4px;">🚀 1-Click Publishing Complete:</div>`;
            for (const [plat, r] of Object.entries(results)) {
                const icon = r.status === 'success' ? '✅' : (r.status === 'warning' ? '⚠️' : '❌');
                htmlMsg += `<div>${icon} <strong>${r.platform || plat}:</strong> ${r.message}</div>`;
            }
            toast.innerHTML = htmlMsg;
        } else {
            toast.innerHTML = `❌ Publishing failed: ${data.detail || 'Error'}`;
        }
    } catch (err) {
        toast.innerHTML = `❌ Publishing error: ${err.message}`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-content"><i data-lucide="zap"></i> Publish Selected Video Now</span>`;
        lucide.createIcons();
    }
}

// Initial Window Load
window.addEventListener('DOMContentLoaded', () => {
    updateHistoryBadge();
    updateSocialNavStatus();
});
