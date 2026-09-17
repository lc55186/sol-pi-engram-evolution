/**
 * BOSS-AI-R 实时副驾 — 前端交互脚本
 * 
 * 功能：
 * 1. WebSocket 连接管理（自动重连、心跳）
 * 2. 录音控制（开始/暂停/结束）
 * 3. 实时转写展示（逐条滚动、说话人标签）
 * 4. 情绪曲线更新（唤醒度/效价/确定度）
 * 5. 提示队列管理（分级展示、手表震动模拟）
 * 6. 说话人状态动画
 */

'use strict';

// ===== 全局状态 =====
const state = {
    sessionId: null,
    isRecording: false,
    isPaused: false,
    ws: null,
    startTime: null,
    elapsed: 0,
    timer: null,
    prompts: [],
    wordCount: 0,
    stats: {
        duration: '00:00',
        words: 0,
        prompts: 0,
        latency: 0
    },
    emotion: {
        arousal: 0.3,
        valence: 0.5,
        confidence: 0.6
    },
    speakers: {
        owner: { active: false, lastActive: 0 },
        opponent: { active: false, lastActive: 0 },
        other: { active: false, lastActive: 0 }
    }
};

// ===== DOM 引用 =====
const dom = {
    circle: document.getElementById('recording-circle'),
    time: document.getElementById('recording-time'),
    btnStart: document.getElementById('btn-start'),
    btnPause: document.getElementById('btn-pause'),
    btnStop: document.getElementById('btn-stop'),
    status: document.getElementById('recording-status'),
    scene: document.getElementById('scene-select'),
    transcript: document.getElementById('transcript-container'),
    wordCount: document.getElementById('word-count'),
    promptList: document.getElementById('prompt-list'),
    promptCount: document.getElementById('prompt-count'),
    watchScreen: document.getElementById('watch-screen'),
    watchContent: document.getElementById('watch-content'),
    arousalBar: document.getElementById('arousal-bar'),
    arousalVal: document.getElementById('arousal-value'),
    valenceBar: document.getElementById('valence-bar'),
    valenceVal: document.getElementById('valence-value'),
    confidenceBar: document.getElementById('confidence-bar'),
    confidenceVal: document.getElementById('confidence-value'),
    emotionEvents: document.getElementById('emotion-events'),
    statDuration: document.getElementById('stat-duration'),
    statWords: document.getElementById('stat-words'),
    statPrompts: document.getElementById('stat-prompts'),
    statLatency: document.getElementById('stat-latency')
};

// ===== API 调用 =====
const api = {
    async post(url, data = {}) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    },
    
    async get(url) {
        const res = await fetch(url);
        return res.json();
    }
};

// ===== 录音控制 =====
async function startRecording() {
    if (state.isRecording) return;
    
    const scene = dom.scene ? dom.scene.value : 'business_negotiation';
    
    try {
        // 调用 API 开始录音
        const result = await api.post('/api/v1/recording/start', {
            tenant_id: 'demo-tenant-001',
            user_id: 'demo-user-001',
            scene: scene,
            platform: 'web'
        });
        
        if (result.session_id) {
            state.sessionId = result.session_id;
            state.isRecording = true;
            state.isPaused = false;
            state.startTime = Date.now();
            
            // 更新 UI
            updateUIState('recording');
            
            // 启动计时器
            startTimer();
            
            // 连接 WebSocket
            connectWebSocket(result.session_id);
            
            // 清空转写
            clearTranscript();
            
            // 启动模拟（Demo 模式）
            startDemoSimulation();
            
            showNotification('录音已开始', 'success');
        }
    } catch (err) {
        console.error('Failed to start recording:', err);
        showNotification('启动失败: ' + err.message, 'error');
    }
}

function pauseRecording() {
    if (!state.isRecording || state.isPaused) return;
    
    state.isPaused = true;
    stopTimer();
    updateUIState('paused');
    
    if (state.ws) {
        state.ws.send(JSON.stringify({ type: 'pause' }));
    }
}

function resumeRecording() {
    if (!state.isRecording || !state.isPaused) return;
    
    state.isPaused = false;
    startTimer();
    updateUIState('recording');
    
    if (state.ws) {
        state.ws.send(JSON.stringify({ type: 'resume' }));
    }
}

async function stopRecording() {
    if (!state.isRecording) return;
    
    try {
        await api.post(`/api/v1/recording/${state.sessionId}/stop`);
    } catch (e) {
        // Demo 模式忽略错误
    }
    
    state.isRecording = false;
    state.isPaused = false;
    
    stopTimer();
    updateUIState('stopped');
    disconnectWebSocket();
    stopDemoSimulation();
    
    showNotification('录音已结束，正在生成纪要...', 'success');
}

// ===== UI 状态管理 =====
function updateUIState(status) {
    if (!dom.circle) return;
    
    switch (status) {
        case 'recording':
            dom.circle.classList.add('active');
            if (dom.btnStart) { dom.btnStart.disabled = true; dom.btnStart.textContent = '🎙️ 录音中'; }
            if (dom.btnPause) { dom.btnPause.disabled = false; dom.btnPause.textContent = '⏸ 暂停'; }
            if (dom.btnStop) dom.btnStop.disabled = false;
            if (dom.status) { dom.status.textContent = '录音中'; dom.status.className = 'badge tag-red'; }
            break;
            
        case 'paused':
            dom.circle.classList.remove('active');
            if (dom.btnPause) { dom.btnPause.disabled = false; dom.btnPause.textContent = '▶ 继续'; }
            if (dom.status) { dom.status.textContent = '已暂停'; dom.status.className = 'badge tag-orange'; }
            break;
            
        case 'stopped':
            dom.circle.classList.remove('active');
            if (dom.btnStart) { dom.btnStart.disabled = false; dom.btnStart.textContent = '▶ 开始'; }
            if (dom.btnPause) { dom.btnPause.disabled = true; dom.btnPause.textContent = '⏸ 暂停'; }
            if (dom.btnStop) dom.btnStop.disabled = true;
            if (dom.status) { dom.status.textContent = '已结束'; dom.status.className = 'badge tag-green'; }
            break;
    }
}

// ===== 计时器 =====
function startTimer() {
    if (state.timer) return;
    
    state.timer = setInterval(() => {
        state.elapsed = Math.floor((Date.now() - state.startTime) / 1000);
        const m = Math.floor(state.elapsed / 60);
        const s = state.elapsed % 60;
        const timeStr = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        
        if (dom.time) dom.time.textContent = timeStr;
        if (dom.statDuration) dom.statDuration.textContent = timeStr;
        
        // 模拟情绪更新
        updateEmotionDisplay();
    }, 1000);
}

function stopTimer() {
    if (state.timer) {
        clearInterval(state.timer);
        state.timer = null;
    }
}

// ===== WebSocket =====
function connectWebSocket(sessionId) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws/realtime/${sessionId}`;
    
    try {
        state.ws = new WebSocket(wsUrl);
        
        state.ws.onopen = () => {
            console.log('WebSocket connected');
            // 启动心跳
            state.ws.send(JSON.stringify({ type: 'ping' }));
        };
        
        state.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWSMessage(data);
            } catch (e) {
                console.error('WS message parse error:', e);
            }
        };
        
        state.ws.onclose = () => {
            console.log('WebSocket disconnected');
            // 自动重连（如果仍在录音）
            if (state.isRecording && !state.isPaused) {
                setTimeout(() => connectWebSocket(sessionId), 3000);
            }
        };
        
        state.ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    } catch (e) {
        console.error('WebSocket connection failed:', e);
    }
}

function disconnectWebSocket() {
    if (state.ws) {
        state.ws.close();
        state.ws = null;
    }
}

function handleWSMessage(data) {
    switch (data.type) {
        case 'realtime_update':
            if (data.asr) addTranscriptLine(data.asr);
            if (data.emotion) updateEmotion(data.emotion);
            if (data.prompt) addPrompt(data.prompt);
            break;
        case 'pong':
            // 心跳响应
            break;
    }
}

// ===== 转写展示 =====
function addTranscriptLine(asr) {
    if (!dom.transcript) return;
    
    // 清空占位符
    const empty = dom.transcript.querySelector('.transcript-empty');
    if (empty) empty.remove();
    
    const line = document.createElement('div');
    line.className = `transcript-line ${asr.speaker}`;
    
    const speakerName = asr.speaker === 'owner' ? '李总（您）' : '王采购（对方）';
    const time = formatTime(state.elapsed);
    
    line.innerHTML = `
        <span class="speaker-tag ${asr.speaker}">${speakerName}</span>
        ${escapeHtml(asr.text)}
        <span class="time-tag">${time}</span>
    `;
    
    dom.transcript.appendChild(line);
    dom.transcript.scrollTop = dom.transcript.scrollHeight;
    
    // 更新字数
    state.wordCount += (asr.text || '').length;
    if (dom.wordCount) dom.wordCount.textContent = `${state.wordCount} 字`;
    if (dom.statWords) dom.statWords.textContent = state.wordCount;
    
    // 说话人动画
    if (asr.speaker) {
        animateSpeaker(asr.speaker);
    }
}

function clearTranscript() {
    if (!dom.transcript) return;
    dom.transcript.innerHTML = '<div class="transcript-empty">正在监听...</div>';
    state.wordCount = 0;
    if (dom.wordCount) dom.wordCount.textContent = '0 字';
}

// ===== 情绪更新 =====
function updateEmotion(emotion) {
    if (!emotion) return;
    
    state.emotion.arousal = emotion.arousal;
    state.emotion.valence = emotion.valence;
    state.emotion.confidence = emotion.confidence;
    
    updateEmotionDisplay();
}

function updateEmotionDisplay() {
    // 模拟波动
    const t = Date.now() / 1000;
    const arousal = 0.3 + 0.3 * Math.sin(t * 0.5) + Math.random() * 0.1;
    const valence = 0.5 + 0.2 * Math.cos(t * 0.3) + Math.random() * 0.1;
    const confidence = 0.6 + 0.2 * Math.sin(t * 0.2);
    
    if (dom.arousalBar) dom.arousalBar.style.width = Math.min(100, arousal * 100) + '%';
    if (dom.arousalVal) dom.arousalVal.textContent = arousal.toFixed(2);
    if (dom.valenceBar) dom.valenceBar.style.width = Math.min(100, valence * 100) + '%';
    if (dom.valenceVal) dom.valenceVal.textContent = valence.toFixed(2);
    if (dom.confidenceBar) dom.confidenceBar.style.width = Math.min(100, confidence * 100) + '%';
    if (dom.confidenceVal) dom.confidenceVal.textContent = confidence.toFixed(2);
}

// ===== 提示队列 =====
function addPrompt(prompt) {
    if (!dom.promptList) return;
    
    // 清空占位符
    const empty = dom.promptList.querySelector('.prompt-empty');
    if (empty) empty.remove();
    
    const item = document.createElement('div');
    item.className = `prompt-item ${prompt.priority}`;
    
    const typeLabels = {
        'keyword_alert': '⚠️ 关键词预警',
        'emotion_signal': '🎭 情绪信号',
        'risk': '🚨 风险提示',
        'opportunity': '💡 商机信号',
        'interjection_suggest': '💬 插话建议'
    };
    
    item.innerHTML = `
        <div class="prompt-type">${typeLabels[prompt.event_type] || '⚡ 提示'}</div>
        <div class="prompt-content">${escapeHtml(prompt.content)}</div>
        <div class="prompt-evidence">📝 ${escapeHtml(prompt.evidence || '')}</div>
        <div class="prompt-channels">${(prompt.channels || []).map(c => `<span class="tag tag-blue">${c}</span>`).join('')}</div>
    `;
    
    dom.promptList.insertBefore(item, dom.promptList.firstChild);
    
    // 更新计数
    state.prompts.push(prompt);
    if (dom.promptCount) dom.promptCount.textContent = `${state.prompts.length} 条`;
    if (dom.statPrompts) dom.statPrompts.textContent = state.prompts.length;
    
    // 手表反馈
    triggerWatchFeedback(prompt);
    
    // 延迟统计
    if (dom.statLatency) dom.statLatency.textContent = (800 + Math.random() * 1200).toFixed(0) + 'ms';
}

// ===== 手表反馈 =====
function triggerWatchFeedback(prompt) {
    if (!dom.watchScreen || !dom.watchContent) return;
    
    dom.watchScreen.classList.add('active');
    dom.watchContent.innerHTML = `
        <span class="watch-icon">📳</span>
        <span class="watch-text">${escapeHtml(prompt.content.substring(0, 12))}</span>
    `;
    
    setTimeout(() => {
        dom.watchScreen.classList.remove('active');
        dom.watchContent.innerHTML = '<span class="watch-icon">⌚</span><span class="watch-text">等待震动...</span>';
    }, 3000);
}

// ===== 说话人动画 =====
function animateSpeaker(speakerId) {
    const speakerMap = { owner: 'speaker-owner', opponent: 'speaker-opponent', other: 'speaker-other' };
    const el = document.getElementById(speakerMap[speakerId]);
    if (!el) return;
    
    el.classList.add('talking');
    setTimeout(() => el.classList.remove('talking'), 2000);
}

// ===== Demo 模拟 =====
let demoInterval = null;

function startDemoSimulation() {
    const demoTexts = [
        { speaker: 'opponent', text: '李总，这次我们希望账期能放到 60 天。' },
        { speaker: 'owner', text: '60 天太长了，我们公司一般 30 天。' },
        { speaker: 'opponent', text: '上次我们订的那批货，质量有点小问题啊...' },
        { speaker: 'owner', text: '哪批货？你说的是 7 月份那 200 件？' },
        { speaker: 'opponent', text: '就是那批。我们客户那边反馈说有 5% 的不良率。' },
        { speaker: 'owner', text: '5%？我们的检验记录是 1.5% 啊。' },
        { speaker: 'opponent', text: '你看这样，账期 60 天，不良品我们各担一半。' },
        { speaker: 'owner', text: '那我得回去跟财务商量一下。' },
        { speaker: 'opponent', text: '行，但本周得给我答复，我们还有一家在谈。' }
    ];
    
    let idx = 0;
    demoInterval = setInterval(() => {
        if (!state.isRecording || state.isPaused) return;
        if (idx >= demoTexts.length) {
            stopDemoSimulation();
            stopRecording();
            return;
        }
        
        const line = demoTexts[idx];
        addTranscriptLine({ text: line.text, speaker: line.speaker, confidence: 0.9 });
        
        // 模拟提示触发
        if (idx === 0) {
            addPrompt({
                event_type: 'keyword_alert',
                priority: 'high',
                content: '⚠️ 账期风险：对方要求 60 天 vs 我方 30 天',
                evidence: '"账期能放到 60 天"',
                channels: ['vibration', 'watch', 'lockscreen']
            });
        } else if (idx === 4) {
            addPrompt({
                event_type: 'keyword_alert',
                priority: 'high',
                content: '⚠️ 质量争议：对方称 5% 不良 vs 我方记录 1.5%',
                evidence: '"5% 的不良率"',
                channels: ['watch', 'lockscreen']
            });
        } else if (idx === 8) {
            addPrompt({
                event_type: 'opportunity',
                priority: 'medium',
                content: '💡 商机信号：对方在比价，可抢先签约',
                evidence: '"还有一家在谈"',
                channels: ['lockscreen']
            });
        }
        
        idx++;
    }, 3500);
}

function stopDemoSimulation() {
    if (demoInterval) {
        clearInterval(demoInterval);
        demoInterval = null;
    }
}

// ===== 工具函数 =====
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.opacity = '0';
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('BOSS-AI-R 实时副驾 已加载');
    
    // 绑定暂停/继续切换
    if (dom.btnPause) {
        dom.btnPause.addEventListener('click', () => {
            if (state.isPaused) {
                resumeRecording();
            } else {
                pauseRecording();
            }
        });
    }
    
    // 情绪启用开关
    const emotionEnabled = document.getElementById('emotion-enabled');
    if (emotionEnabled) {
        emotionEnabled.addEventListener('change', (e) => {
            if (e.target.checked) {
                showNotification('情绪分析已启用（仅描述声学现象）', 'info');
            }
        });
    }
});
