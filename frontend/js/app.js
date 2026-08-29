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
    const storyStyle = document.getElementById('config-story-style')?.value || 'untold_story';

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
        voice_id: voiceId,
        story_style: storyStyle,
        num_reels: numReels,
        max_analysis_duration: analysisRangeVal > 0 ? analysisRangeVal : null,
        layout_mode: 'blur_canvas',
        caption_theme: theme,
        caption_position: position,
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

        const tagsHtml = (reel.hashtags || []).map(t => `<span class="reel-tag">${t}</span>`).join('');

        card.innerHTML = `
            <div class="reel-card-header">
                <span class="virality-chip">🔥 ${reel.virality_score}/100 Virality</span>
                <span class="duration-chip"><i data-lucide="clock" style="width:12px;display:inline;"></i> ${Math.round(reel.duration)}s</span>
            </div>
            <h4 class="reel-card-title">${reel.title}</h4>
            <p class="reel-card-hook">${reel.hook || reel.text.slice(0, 80) + '...'}</p>
            <div class="reel-card-tags">
                ${tagsHtml}
            </div>
        `;
        container.appendChild(card);
    });

    lucide.createIcons();
}

let currentSocialPlatform = 'instagram';

// Select Active Reel for Studio Preview & Editing
function selectReel(index) {
    activeReelIndex = index;
    const reel = currentReelsData[index];
    if (!reel) return;

    // Highlight card
    const cards = document.querySelectorAll('.reel-card');
    cards.forEach((c, idx) => {
        if (idx === index) c.classList.add('active');
        else c.classList.remove('active');
    });

    // Update Player & Header
    const videoElem = document.getElementById('main-reel-video');
    videoElem.src = reel.video_url;
    videoElem.load();
    videoElem.play().catch(() => {});

    document.getElementById('active-clip-title').textContent = reel.title;
    document.getElementById('active-virality-chip').textContent = `🔥 ${reel.virality_score}/100 Viral Score`;
    document.getElementById('btn-direct-download').href = reel.download_url;

    // Update Customizer Inputs
    document.getElementById('edit-start-time').value = reel.start_time;
    document.getElementById('edit-end-time').value = reel.end_time;
    document.getElementById('edit-theme').value = reel.caption_theme || 'hormozi';
    document.getElementById('edit-layout').value = reel.layout_mode || 'blur_canvas';
    document.getElementById('edit-position').value = reel.caption_position || 'bottom';

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
