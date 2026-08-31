// AI B-Roll Multi-Clip Story Studio Frontend Logic

let currentScenes = [];
let currentBrollJobId = null;
let currentRenderedReel = null;
let progressInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = localStorage.getItem('ai_script_api_key');
    if (savedKey && document.getElementById('user-ai-api-key')) {
        document.getElementById('user-ai-api-key').value = savedKey;
    }
    const savedEleven = localStorage.getItem('elevenlabs_voice_key');
    if (savedEleven && document.getElementById('user-elevenlabs-key')) {
        document.getElementById('user-elevenlabs-key').value = savedEleven;
    }
});

function saveAiApiKey(val) {
    if (val && val.trim()) {
        localStorage.setItem('ai_script_api_key', val.trim());
    } else {
        localStorage.removeItem('ai_script_api_key');
    }
}

function getAiApiKey() {
    const el = document.getElementById('user-ai-api-key');
    if (el && el.value.trim()) return el.value.trim();
    return localStorage.getItem('ai_script_api_key') || null;
}

function saveElevenLabsKey(val) {
    if (val && val.trim()) {
        localStorage.setItem('elevenlabs_voice_key', val.trim());
    } else {
        localStorage.removeItem('elevenlabs_voice_key');
    }
}

function getElevenLabsKey() {
    const el = document.getElementById('user-elevenlabs-key');
    if (el && el.value.trim()) return el.value.trim();
    return localStorage.getItem('elevenlabs_voice_key') || null;
}

function setTopic(topic, niche) {
    document.getElementById('story-topic-input').value = topic;
    if (document.getElementById('timeline-topic-input')) {
        document.getElementById('timeline-topic-input').value = topic;
    }
    if (niche) document.getElementById('config-niche').value = niche;
    generateStoryScript();
}

function syncDurationMode(val) {
    const topSelect = document.getElementById('config-duration-mode');
    const timelineSelect = document.getElementById('timeline-duration-mode');
    if (topSelect) topSelect.value = val;
    if (timelineSelect) timelineSelect.value = val;
}

function onNicheChange() {
    // Optionally trigger re-generation or update defaults
}

// 1. Generate Scene-by-Scene Script Breakdown
async function generateStoryScript() {
    const topic = document.getElementById('story-topic-input').value.trim();
    const niche = document.getElementById('config-niche').value;
    const durationMode = document.getElementById('config-duration-mode') ? document.getElementById('config-duration-mode').value : 'long';
    const apiKey = getAiApiKey();
    const btn = document.getElementById('btn-generate-script');

    if (!topic) {
        alert('Please enter a topic or select one of the viral prompts.');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Generating Unique Script...`;
    lucide.createIcons();

    try {
        const res = await fetch('/api/broll/generate-script', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                topic, 
                niche, 
                language: 'hinglish',
                duration_mode: durationMode,
                api_key: apiKey
            })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            currentScenes = data.data.scenes || [];
            if (document.getElementById('timeline-topic-input')) {
                document.getElementById('timeline-topic-input').value = topic;
            }
            renderSceneTimeline(currentScenes);
            document.getElementById('scene-timeline-section').classList.remove('hidden');
            window.location.hash = 'scene-timeline-section';
        } else {
            alert(`Script generation failed: ${data.detail || 'Error'}`);
        }
    } catch (err) {
        alert(`Error generating script: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="wand-2"></i> Auto-Script Scenes`;
        lucide.createIcons();
    }
}

// Generate scenes directly from the timeline topic bar
async function generateStoryScriptFromTimeline() {
    const topicInput = document.getElementById('timeline-topic-input');
    const topic = topicInput ? topicInput.value.trim() : (document.getElementById('story-topic-input').value.trim() || 'Deep Story');
    const niche = document.getElementById('config-niche').value;
    const durationMode = document.getElementById('timeline-duration-mode') ? document.getElementById('timeline-duration-mode').value : 'long';
    const customPrompt = document.getElementById('timeline-custom-prompt') ? document.getElementById('timeline-custom-prompt').value.trim() : '';
    const apiKey = getAiApiKey();

    if (!topic) {
        alert('Please enter a topic to create scenes.');
        return;
    }

    const res = await fetch('/api/broll/generate-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            topic,
            niche,
            language: 'hinglish',
            duration_mode: durationMode,
            custom_prompt: customPrompt || null,
            api_key: apiKey
        })
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
        currentScenes = data.data.scenes || [];
        document.getElementById('story-topic-input').value = topic;
        renderSceneTimeline(currentScenes);
        alert(`✅ Generated ${currentScenes.length} unique explanatory scenes (~${data.data.estimated_duration}s)!`);
    } else {
        alert(`Failed: ${data.detail || 'Error'}`);
    }
}

// Render Scene Timeline Cards
function renderSceneTimeline(scenes) {
    const container = document.getElementById('scenes-list-container');
    container.innerHTML = '';

    scenes.forEach((scene, index) => {
        const card = document.createElement('div');
        card.className = 'scene-card';
        card.id = `scene-card-${index}`;
        
        const roleIcons = {
            hook: '🔥 Hook',
            problem: '⚠️ Conflict',
            conflict: '⚡ Tension',
            reveal: '💡 Reveal',
            payoff: '💰 Climax',
            cta: '🎯 Call-to-Action',
            context: '📜 Context',
            mechanism_1: '⚙️ Principle 1',
            mechanism_2: '🧠 Principle 2',
            mechanism_3: '💡 Principle 3',
            psychological_trap: '🔮 Mind Trap',
            surveillance: '📊 Tracking',
            financial_math: '📈 Math & Edge',
            sunk_cost: '⏳ Sunk Cost',
            real_example: '🏢 Case Study',
            defense_strategy: '🛡️ Defense',
            actionable_rule: '📋 Master Rule',
            mindset_shift: '✨ Mindset Shift',
            conclusion: '🎯 Takeaway'
        };

        const clipBadge = scene.selected_clip ? `
            <div class="selected-clip-preview" style="display:flex; align-items:center; gap:10px; font-size:11px; background:rgba(0,255,163,0.08); border:1px solid rgba(0,255,163,0.25); color:#00ffa3; padding:6px 12px; border-radius:6px; margin-top:8px;">
                <img src="${scene.selected_clip.thumbnail}" style="width:34px; height:34px; border-radius:4px; object-fit:cover; border:1px solid rgba(0,255,163,0.3);">
                <div style="flex:1;">
                    <div>📱 <strong>Pexels 9:16 Portrait</strong>: ${scene.selected_clip.title}</div>
                    <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">Duration: ${scene.selected_clip.duration || 5}s • Creator: ${scene.selected_clip.author || 'Pexels'}</div>
                </div>
                <button class="btn-action" style="padding:3px 8px; font-size:10px;" onclick="testSearchClip(${index})">🔄 Change Clip</button>
            </div>
        ` : '';

        const roleLabel = roleIcons[scene.role] || `Scene #${index + 1}`;
        const chapterHeader = scene.chapter ? `<div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">${scene.chapter}</div>` : '';
        const durLabel = scene.target_duration ? `<span style="font-size: 11px; color: var(--text-muted); margin-left: 6px;">(~${scene.target_duration}s)</span>` : '';

        card.innerHTML = `
            <div class="scene-number-col">
                <div class="scene-badge-num">${index + 1}</div>
                <span class="scene-role-tag">${roleLabel}</span>
            </div>
            <div class="scene-main-content">
                ${chapterHeader}
                <textarea class="scene-script-textarea" rows="3" style="min-height: 60px;" onchange="updateSceneScript(${index}, this.value)">${scene.script_hi || scene.script_en || ''}</textarea>
                <div class="scene-broll-row">
                    <label><i data-lucide="video"></i> Visual Query:${durLabel}</label>
                    <input type="text" class="scene-query-input" value="${scene.search_query || ''}" onchange="updateSceneQuery(${index}, this.value)">
                    <button class="btn-search-clips" onclick="testSearchClip(${index})"><i data-lucide="search"></i> Match Pexels Clips</button>
                </div>
                ${clipBadge}
                <div id="clip-picker-drawer-${index}" class="clip-picker-drawer hidden" style="margin-top:10px; padding:10px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.08); border-radius:8px;"></div>
            </div>
            <button class="scene-card-del" title="Remove scene" onclick="removeScene(${index})"><i data-lucide="trash-2"></i></button>
        `;
        container.appendChild(card);
    });
    lucide.createIcons();
}

function updateSceneScript(index, val) {
    if (currentScenes[index]) currentScenes[index].script_hi = val;
}

function updateSceneQuery(index, val) {
    if (currentScenes[index]) currentScenes[index].search_query = val;
}

function removeScene(index) {
    if (currentScenes.length <= 2) {
        alert('A reel needs at least 2 scenes.');
        return;
    }
    currentScenes.splice(index, 1);
    renderSceneTimeline(currentScenes);
}

function addNewScene() {
    currentScenes.push({
        scene_number: currentScenes.length + 1,
        role: "conflict",
        script_hi: "यहाँ आपका नया डायलॉग आएगा...",
        script_en: "Enter next scene script line here...",
        search_query: "cinematic business dark dramatic",
        target_duration: 4.0,
        sfx: "whoosh"
    });
    renderSceneTimeline(currentScenes);
}

async function testSearchClip(index) {
    const scene = currentScenes[index];
    if (!scene) return;
    const query = scene.search_query || 'cinematic';
    const drawer = document.getElementById(`clip-picker-drawer-${index}`);
    
    if (drawer) {
        drawer.classList.remove('hidden');
        drawer.innerHTML = `<div style="font-size:11px; color:var(--text-muted); display:flex; align-items:center; gap:6px;"><i data-lucide="loader-2" class="spin"></i> Searching 9:16 Pexels clips for "${query}"...</div>`;
        lucide.createIcons();
    }
    
    try {
        const res = await fetch('/api/broll/search-clips', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, count: 6 })
        });
        const data = await res.json();
        if (res.ok && data.clips && data.clips.length > 0) {
            let gridHtml = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:11px; font-weight:600; color:var(--accent-cyan);">Choose Video Clip for Scene #${index + 1}:</span>
                    <button style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:11px;" onclick="document.getElementById('clip-picker-drawer-${index}').classList.add('hidden')">✕ Close</button>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(130px, 1fr)); gap:8px;">
            `;
            data.clips.forEach((clip, clipIdx) => {
                gridHtml += `
                    <div style="cursor:pointer; border:1px solid rgba(255,255,255,0.1); border-radius:6px; overflow:hidden; background:rgba(255,255,255,0.03); transition:all 0.2s;" onmouseover="this.style.borderColor='#00ffa3'" onmouseout="this.style.borderColor='rgba(255,255,255,0.1)'" onclick="selectSpecificClip(${index}, ${clipIdx}, ${JSON.stringify(clip).replace(/"/g, '&quot;')})">
                        <img src="${clip.thumbnail}" style="width:100%; height:75px; object-fit:cover; display:block;">
                        <div style="padding:4px 6px; font-size:10px; color:var(--text-secondary); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">${clip.title}</div>
                    </div>
                `;
            });
            gridHtml += `</div>`;
            if (drawer) {
                drawer.innerHTML = gridHtml;
            }
        } else {
            if (drawer) {
                drawer.innerHTML = `<div style="font-size:11px; color:var(--text-muted);">No portrait clips found for "${query}". Try adjusting keywords.</div>`;
            }
        }
    } catch (err) {
        alert(`Search error: ${err.message}`);
    }
}

function selectSpecificClip(sceneIndex, clipIndex, clipObj) {
    if (currentScenes[sceneIndex]) {
        currentScenes[sceneIndex].selected_clip = clipObj;
        renderSceneTimeline(currentScenes);
    }
}

// 2. Start Master Multi-Clip 9:16 Render
async function startMasterBrollRender() {
    if (!currentScenes || currentScenes.length === 0) {
        alert('Please generate a script breakdown first.');
        return;
    }

    const topic = document.getElementById('story-topic-input').value.trim() || 'Viral Story';
    const voiceId = document.getElementById('config-voice').value;
    const audioVibe = document.getElementById('config-audio-vibe').value;
    const captionTheme = document.getElementById('config-theme').value;
    const elevenlabsKey = getElevenLabsKey();

    const btn = document.getElementById('btn-synthesize-master');
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-content"><i data-lucide="loader-2" class="spin"></i> Starting Multi-Clip Synthesizer...</span>`;
    lucide.createIcons();

    document.getElementById('progress-section').classList.remove('hidden');
    document.getElementById('studio-section').classList.add('hidden');
    window.location.hash = 'progress-section';

    const framingMode = document.getElementById('config-framing') ? document.getElementById('config-framing').value : 'full_screen';

    const payload = {
        topic: topic,
        scenes: currentScenes,
        voice_id: voiceId,
        audio_vibe: audioVibe,
        caption_theme: captionTheme,
        caption_position: 'bottom',
        language_mode: 'hindi',
        framing_mode: framingMode,
        elevenlabs_api_key: elevenlabsKey
    };

    try {
        const res = await fetch('/api/broll/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
            currentBrollJobId = data.job_id;
            pollBrollProgress(currentBrollJobId);
        } else {
            alert(`Render failed: ${data.detail || 'Error'}`);
            btn.disabled = false;
            btn.innerHTML = `<span class="btn-content"><i data-lucide="sparkles"></i> Render Multi-Clip 9:16 Viral Reel</span>`;
            lucide.createIcons();
        }
    } catch (err) {
        alert(`Render error: ${err.message}`);
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-content"><i data-lucide="sparkles"></i> Render Multi-Clip 9:16 Viral Reel</span>`;
        lucide.createIcons();
    }
}

// 3. Poll Progress
function pollBrollProgress(jobId) {
    if (progressInterval) clearInterval(progressInterval);

    progressInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/broll/progress/${jobId}`);
            const data = await res.json();

            const percent = Math.round(data.percent || 0);
            document.getElementById('progress-percent').textContent = `${percent}%`;
            document.getElementById('progress-bar-fill').style.width = `${percent}%`;
            document.getElementById('progress-detail-msg').textContent = data.message || 'Processing...';

            if (data.status === 'completed') {
                clearInterval(progressInterval);
                onBrollComplete(data);
            } else if (data.status === 'error') {
                clearInterval(progressInterval);
                alert(`Rendering error: ${data.message || data.error}`);
                const btn = document.getElementById('btn-synthesize-master');
                btn.disabled = false;
                btn.innerHTML = `<span class="btn-content"><i data-lucide="sparkles"></i> Render Multi-Clip 9:16 Viral Reel</span>`;
                lucide.createIcons();
            }
        } catch (err) {
            console.warn('Broll progress poll error:', err);
        }
    }, 1200);
}

// 4. On Render Complete
function onBrollComplete(data) {
    const reels = data.reels || [];
    if (reels.length === 0) {
        alert('No reel output found.');
        return;
    }

    currentRenderedReel = reels[0];

    const videoElem = document.getElementById('main-broll-video');
    videoElem.src = currentRenderedReel.video_url;
    videoElem.load();
    videoElem.play().catch(() => {});

    document.getElementById('broll-reel-title').textContent = currentRenderedReel.title;
    document.getElementById('btn-download-reel').href = currentRenderedReel.download_url;

    // Reset publish toast
    const toast = document.getElementById('publish-result-toast');
    if (toast) toast.classList.add('hidden');

    document.getElementById('progress-section').classList.add('hidden');
    document.getElementById('studio-section').classList.remove('hidden');
    window.location.hash = 'studio-section';

    const btn = document.getElementById('btn-synthesize-master');
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-content"><i data-lucide="sparkles"></i> Render Multi-Clip 9:16 Viral Reel</span>`;
    lucide.createIcons();

    updateHistoryBadge();
}

function resetBrollStudio() {
    document.getElementById('studio-section').classList.add('hidden');
    document.getElementById('progress-section').classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 1-Click Social Publishing for B-Roll Reel
async function publishActiveBrollReel() {
    if (!currentRenderedReel) {
        alert('No rendered reel available.');
        return;
    }

    const selectedPlatforms = [];
    if (document.getElementById('pub-check-ig')?.checked) selectedPlatforms.push('instagram');
    if (document.getElementById('pub-check-yt')?.checked) selectedPlatforms.push('youtube');
    if (document.getElementById('pub-check-tw')?.checked) selectedPlatforms.push('twitter');
    if (document.getElementById('pub-check-tt')?.checked) selectedPlatforms.push('tiktok');
    if (document.getElementById('pub-check-hook')?.checked) selectedPlatforms.push('webhook');

    if (selectedPlatforms.length === 0) {
        alert('Please select at least one social media platform.');
        return;
    }

    const btn = document.getElementById('btn-publish-now');
    const toast = document.getElementById('publish-result-toast');
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-content"><i data-lucide="loader-2" class="spin"></i> Publishing to ${selectedPlatforms.length} Platform(s)...</span>`;
    lucide.createIcons();

    toast.classList.remove('hidden');
    toast.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Uploading video and pushing to social feeds...`;
    lucide.createIcons();

    try {
        const res = await fetch('/api/social/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platforms: selectedPlatforms,
                reel: currentRenderedReel,
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
        btn.innerHTML = `<span class="btn-content"><i data-lucide="zap"></i> Publish Master Reel Now</span>`;
        lucide.createIcons();
    }
}

// History & Social Modals Helpers
async function openHistoryDrawer() {
    const drawer = document.getElementById('history-drawer');
    const overlay = document.getElementById('history-overlay');
    drawer.classList.remove('hidden');
    overlay.classList.remove('hidden');

    const container = document.getElementById('history-list-container');
    container.innerHTML = `<div class="history-empty"><i data-lucide="loader-2" class="spin"></i><p>Loading...</p></div>`;
    lucide.createIcons();

    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const items = data.history || [];

        if (items.length === 0) {
            container.innerHTML = `<div class="history-empty"><i data-lucide="film"></i><p>No history yet.</p></div>`;
        } else {
            container.innerHTML = '';
            items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'history-card';
                const thumb = item.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&auto=format&fit=crop&q=60';
                card.innerHTML = `
                    <img src="${thumb}" class="history-thumb" alt="Thumb" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&auto=format&fit=crop&q=60'">
                    <div class="history-card-info" onclick="loadHistoryJobToBroll('${item.job_id}')">
                        <div class="history-card-title">${item.title}</div>
                        <div class="history-card-meta"><span>📅 ${item.created_at || 'Recently'}</span></div>
                        <span class="history-reels-count">🎬 ${item.reels_count} Reel(s)</span>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (err) {
        container.innerHTML = `<p>Error: ${err.message}</p>`;
    }
    lucide.createIcons();
}

function closeHistoryDrawer() {
    document.getElementById('history-drawer').classList.add('hidden');
    document.getElementById('history-overlay').classList.add('hidden');
}

async function loadHistoryJobToBroll(jobId) {
    closeHistoryDrawer();
    try {
        const res = await fetch(`/api/history/${jobId}`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            const reels = data.job.reels || [];
            if (reels.length > 0) {
                onBrollComplete({ reels: reels });
            }
        }
    } catch (err) {
        alert(`Failed to load history: ${err.message}`);
    }
}

async function updateHistoryBadge() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        const count = (data.history || []).length;
        const badge = document.getElementById('history-badge');
        if (badge) badge.textContent = count;
    } catch (err) {}
}

async function openSocialModal() {
    const modal = document.getElementById('social-modal');
    const overlay = document.getElementById('social-modal-overlay');
    modal.classList.remove('hidden');
    overlay.classList.remove('hidden');

    try {
        const res = await fetch('/api/social/accounts');
        const data = await res.json();
        const accs = data.accounts || {};
        for (const [plat, conf] of Object.entries(accs)) {
            const badge = document.getElementById(`badge-status-${plat}`);
            if (badge) {
                badge.textContent = conf.connected ? `🟢 Connected (${conf.account_name || 'Active'})` : `⚪ Not Connected`;
                if (conf.connected) badge.classList.add('connected'); else badge.classList.remove('connected');
            }
        }
    } catch (err) {}
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
        if (res.ok) {
            alert(`✅ ${platform.toUpperCase()} settings saved!`);
            openSocialModal();
        }
    } catch (err) {
        alert(`Save error: ${err.message}`);
    }
}

async function disconnectSocialAccount(platform) {
    try {
        const res = await fetch('/api/social/disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform })
        });
        if (res.ok) openSocialModal();
    } catch (err) {}
}

window.addEventListener('DOMContentLoaded', () => {
    updateHistoryBadge();
    // Auto-load default sample script on initial open
    generateStoryScript();
});
