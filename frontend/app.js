/* DramaPulse 高光点验证页 - 核心逻辑 */

/* ========== 全局状态 ========== */
var highlights = [];
var triggeredIds = {};
var currentBranchHl = null;
var audioCtx = null;

/* ========== 工具函数 ========== */
function $(id) { return document.getElementById(id); }

function fmtTime(sec) {
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    return (m < 10 ? '0' + m : '' + m) + ':' + (s < 10 ? '0' + s : '' + s);
}

/* ========== 日志 ========== */
function log(msg, type) {
    type = type || 'info';
    var el = $('log-content');
    var now = new Date();
    var ts = now.toTimeString().slice(0, 8);
    var line = document.createElement('div');
    line.className = 'log-line log-' + type;
    line.innerHTML = '<span class="log-time">[' + ts + ']</span><span class="log-msg">' + msg + '</span>';
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
}

function clearLog() {
    $('log-content').innerHTML = '';
}

/* ========== 加载高光点 ========== */
async function loadHighlights() {
    var base = $('api-base').value.trim().replace(/\/+$/, '');
    var epNo = $('episode-no').value.trim();
    var url = base + '/episodes/' + epNo + '/highlights';
    log('正在请求：' + url, 'info');
    try {
        var resp = await fetch(url);
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        var data = await resp.json();
        highlights = data.highlights || [];
        triggeredIds = {};
        renderHighlightList();
        log('加载成功：' + highlights.length + ' 个高光点', 'trigger');
        $('status-text').textContent = highlights.length + ' 个高光点已加载';
    } catch (e) {
        log('加载失败：' + e.message, 'error');
        $('status-text').textContent = '加载失败，请检查 API 地址';
    }
}

/* ========== 渲染高光点列表 ========== */
function renderHighlightList() {
    var container = $('highlight-list');
    $('hl-count').textContent = highlights.length + ' 个';
    if (highlights.length === 0) {
        container.innerHTML = '<div style="color:#8b949e;font-size:12px;padding:20px;text-align:center;">暂无数据</div>';
        return;
    }
    container.innerHTML = '';
    for (var i = 0; i < highlights.length; i++) {
        var h = highlights[i];
        var card = document.createElement('div');
        card.className = 'hl-card' + (triggeredIds[h.id] ? ' triggered' : '');
        card.id = 'hl-card-' + h.id;
        var tags = '';
        if (h.visual_effect) tags += '<span class="hl-tag effect">' + h.visual_effect + '</span>';
        if (h.particle_type) tags += '<span class="hl-tag">' + h.particle_type + '</span>';
        if (h.haptic_pattern) tags += '<span class="hl-tag">' + h.haptic_pattern + '</span>';
        if (h.audio_cue) tags += '<span class="hl-tag">' + h.audio_cue + '</span>';
        if (h.show_branch) tags += '<span class="hl-tag branch">分支</span>';
        card.innerHTML =
            '<div><span class="hl-time">' + fmtTime(h.timestamp) + '</span>' +
            '<span class="hl-type">' + (h.type || '') + '</span></div>' +
            '<div class="hl-tags">' + tags + '</div>' +
            '<div class="hl-desc">' + (h.scene_desc || '') + '</div>';
        container.appendChild(card);
    }
}

/* ========== 重置触发 ========== */
function resetTriggered() {
    triggeredIds = {};
    clearEffects();
    renderHighlightList();
    log('已重置所有触发状态', 'info');
}

/* ========== 视频选择 ========== */
function onVideoSelected(e) {
    var file = e.target.files[0];
    if (!file) return;
    var url = URL.createObjectURL(file);
    var video = $('video-player');
    video.src = url;
    $('video-name').textContent = file.name;
    log('已加载视频：' + file.name, 'info');
}

/* ========== 从服务器加载视频 ========== */
function loadServerVideo() {
    var base = $('api-base').value.trim().replace(/\/+$/, '');
    var video = $('video-player');
    video.src = base + '/video/stream';
    $('video-name').textContent = '第67集.mp4（服务器流）';
    log('正在从服务器加载视频：' + base + '/video/stream', 'info');
}

/* ========== 播放进度监听 ========== */
$('video-player').addEventListener('timeupdate', function () {
    if (highlights.length === 0) return;
    var currentSec = Math.floor(this.currentTime);
    for (var i = 0; i < highlights.length; i++) {
        var h = highlights[i];
        if (triggeredIds[h.id]) continue;
        if (currentSec >= h.timestamp && currentSec < h.timestamp + 2) {
            triggeredIds[h.id] = true;
            triggerHighlight(h);
            renderHighlightList();
        }
    }
});

/* ========== 触发高光点 ========== */
function triggerHighlight(h) {
    log('触发高光点 #' + h.id + ' @ ' + fmtTime(h.timestamp) + ' - ' + (h.type || '') + ' / ' + (h.emotion || ''), 'trigger');

    if (h.visual_effect) applyVisualEffect(h.visual_effect, h.intensity || 5);
    if (h.particle_type) applyParticleEffect(h.particle_type);
    if (h.haptic_pattern) log('震动模拟：' + h.haptic_pattern, 'effect');
    if (h.audio_cue) playAudioCue(h.audio_cue);
    if (h.show_branch && h.branch_options && h.branch_options.length > 0) {
        videoPauseForBranch(h);
    }

    setTimeout(clearEffects, 3000);
}

/* ========== 视觉特效 ========== */
function applyVisualEffect(effect, intensity) {
    var overlay = $('effect-overlay');
    log('视觉特效：' + effect + ' (强度 ' + intensity + ')', 'effect');

    var el = document.createElement('div');

    if (effect === 'flashlight_flicker') {
        el.className = 'flashlight-flicker';
        el.style.animationDuration = Math.max(0.05, 0.3 - intensity * 0.02) + 's';
        overlay.appendChild(el);
    }

    if (effect === 'heartbeat_pulse') {
        el.className = 'heartbeat-pulse';
        el.style.animationDuration = Math.max(0.3, 1.2 - intensity * 0.05) + 's';
        overlay.appendChild(el);
    }
}

/* ========== 粒子特效 ========== */
function applyParticleEffect(type) {
    var wrapper = $('video-wrapper');
    log('粒子特效：' + type, 'effect');

    if (type === 'dust_mote') {
        for (var i = 0; i < 18; i++) {
            createDustParticle(wrapper, i);
        }
    }

    if (type === 'dark_fog') {
        var overlay = $('effect-overlay');
        var el = document.createElement('div');
        el.className = 'dark-fog';
        overlay.appendChild(el);
    }
}

function createDustParticle(wrapper, idx) {
    var dot = document.createElement('div');
    dot.className = 'dust-particle';
    var size = 2 + Math.random() * 4;
    var opacity = 0.3 + Math.random() * 0.5;
    dot.style.width = size + 'px';
    dot.style.height = size + 'px';
    dot.style.left = Math.random() * 100 + '%';
    dot.style.top = Math.random() * 100 + '%';
    dot.style.background = 'rgba(200,180,140,' + opacity + ')';

    var dx = (Math.random() * 60 - 30) + 'px';
    var dy = (-40 - Math.random() * 80) + 'px';
    var dur = (3 + Math.random() * 4) + 's';
    var animName = 'floatDust' + idx;

    var styleEl = document.createElement('style');
    styleEl.textContent = '@keyframes ' + animName +
        '{0%{transform:translate(0,0);opacity:' + opacity + '}' +
        '100%{transform:translate(' + dx + ',' + dy + ');opacity:0;}}';
    document.head.appendChild(styleEl);

    dot.style.animation = animName + ' ' + dur + ' ease-in-out infinite alternate';
    wrapper.appendChild(dot);

    setTimeout(function () {
        if (dot.parentNode) dot.parentNode.removeChild(dot);
        if (styleEl.parentNode) styleEl.parentNode.removeChild(styleEl);
    }, 8000);
}

/* ========== 清除特效 ========== */
function clearEffects() {
    $('effect-overlay').innerHTML = '';
    var particles = document.querySelectorAll('.dust-particle');
    for (var i = 0; i < particles.length; i++) {
        if (particles[i].parentNode) particles[i].parentNode.removeChild(particles[i]);
    }
}

/* ========== 音效（Web Audio API） ========== */
function playAudioCue(cue) {
    log('音效：' + cue, 'effect');
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        var ctx = audioCtx;
        var osc = ctx.createOscillator();
        var gainNode = ctx.createGain();
        osc.connect(gainNode);
        gainNode.connect(ctx.destination);

        if (cue === 'creak_sound') {
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(120, ctx.currentTime);
            osc.frequency.linearRampToValueAtTime(80, ctx.currentTime + 0.15);
            osc.frequency.linearRampToValueAtTime(130, ctx.currentTime + 0.3);
            gainNode.gain.setValueAtTime(0.15, ctx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.4);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.4);
        } else if (cue === 'low_freq_drone') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(55, ctx.currentTime);
            gainNode.gain.setValueAtTime(0.12, ctx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 1.5);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 1.5);
        } else {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, ctx.currentTime);
            gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.3);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.3);
        }
    } catch (e) {
        log('音效播放失败：' + e.message, 'error');
    }
}

/* ========== 分支弹窗 ========== */
function videoPauseForBranch(h) {
    var video = $('video-player');
    video.pause();
    currentBranchHl = h;

    $('modal-title').textContent = '剧情分支 - ' + fmtTime(h.timestamp);
    $('modal-subtitle').textContent = h.scene_desc || '请选择一个方向';
    $('ai-response').textContent = '';
    $('btn-resume').style.display = 'none';

    // 重置媒体区域（避免上次残留）
    $('ai-image').style.display = 'none';
    $('ai-image-img').src = '';
    $('branch-video-wrap').style.display = 'none';
    var bv = $('branch-video');
    bv.pause();
    bv.src = '';

    var optionsEl = $('branch-options');
    optionsEl.innerHTML = '';
    for (var i = 0; i < h.branch_options.length; i++) {
        var opt = h.branch_options[i];
        var btn = document.createElement('button');
        btn.className = 'branch-btn';
        btn.innerHTML = '<span class="opt-label">' + opt.id + '</span>' + opt.text;
        btn.setAttribute('data-highlight-id', h.id);
        btn.setAttribute('data-branch-id', opt.id);
        btn.onclick = function () {
            onBranchSelected(h, opt);
        };
        optionsEl.appendChild(btn);
    }

    $('branch-modal').classList.add('active');
    log('弹出分支弹窗：高光点 #' + h.id, 'branch');
}

async function onBranchSelected(h, opt) {
    log('选择分支：' + opt.id + ' - ' + opt.text, 'branch');

    var btns = $('branch-options').querySelectorAll('.branch-btn');
    for (var i = 0; i < btns.length; i++) {
        btns[i].disabled = true;
    }

    // 隐藏上一次的媒体内容
    $('ai-image').style.display = 'none';
    $('ai-image-img').src = '';
    $('branch-video-wrap').style.display = 'none';
    var branchVideo = $('branch-video');
    branchVideo.pause();
    branchVideo.src = '';

    var base = $('api-base').value.trim().replace(/\/+$/, '');
    var reqBody = JSON.stringify({
        episode_no: 67,
        highlight_id: h.id,
        branch_id: opt.id,
        branch_text: opt.text
    });

    log('请求 AI 续写...', 'branch');
    try {
        // 优先尝试方案C（预渲染视频），其次方案B（文生图），最后方案A（纯文字）
        var endpoints = ['/ai/branch-video', '/ai/branch-with-image', '/ai/branch'];
        var data = null;
        var errMsg = '';
        for (var ei = 0; ei < endpoints.length; ei++) {
            try {
                var resp = await fetch(base + endpoints[ei], {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: reqBody
                });
                if (resp.ok) {
                    data = await resp.json();
                    log('使用接口：' + endpoints[ei] + '，result_type=' + (data.result_type || 'text'), 'branch');
                    break;
                }
            } catch (e) {
                errMsg = e.message;
            }
        }

        if (!data) {
            throw new Error(errMsg || '所有接口均不可用');
        }

        // 根据 result_type 处理多媒体内容
        var resultType = data.result_type || 'text';
        var aiText = data.text || data.ai_response || '（无返回内容）';
        $('ai-response').textContent = '';

        if (resultType === 'video' && data.media_url) {
            // 方案C：播放预渲染分支视频（不显示文字，直接放视频）
            $('branch-video-wrap').style.display = 'block';
            var vidUrl = data.media_url;
            if (vidUrl && !vidUrl.startsWith('http') && !vidUrl.startsWith('/')) {
                vidUrl = '/' + vidUrl;
            }
            branchVideo.src = vidUrl;
            branchVideo.load();
            log('播放分支视频：' + vidUrl, 'effect');
            branchVideo.onended = function() {
                $('btn-resume').style.display = 'inline-block';
                log('分支视频播放完毕', 'info');
            };
            branchVideo.play();
            $('btn-resume').style.display = 'none';
            log('AI 续写成功（视频分支）', 'branch');
            return;
        }

        if (resultType === 'image' && data.image_url) {
            // 方案B：先显示图片，图片下方文字打字机效果，完毕后出现"继续播放"
            var imgUrl = data.image_url;
            if (imgUrl && !imgUrl.startsWith('http') && !imgUrl.startsWith('/')) {
                imgUrl = '/' + imgUrl;
            }
            $('ai-image').style.display = 'block';
            $('ai-image-img').src = imgUrl;
            log('显示 AI 配图：' + imgUrl, 'effect');
        }

        // 文字打字机效果（方案A纯文字 / 方案B图片+文字都走这里）
        typewriterEffect('ai-response', aiText, function() {
            $('btn-resume').style.display = 'inline-block';
        });

        log('AI 续写成功（tokens: ' + (data.token_usage || '?') + '）', 'branch');

    } catch (e) {
        log('AI 续写失败：' + e.message, 'error');
        $('ai-response').textContent = '请求失败：' + e.message;
        $('btn-resume').style.display = 'inline-block';
    }
}

/* ========== 打字机效果 ========== */
function typewriterEffect(elementId, text, onDone) {
    var el = $(elementId);
    el.textContent = '';
    var i = 0;
    var speed = 35;

    function tick() {
        if (i < text.length) {
            el.textContent += text.charAt(i);
            i++;
            setTimeout(tick, speed);
        } else {
            if (onDone) onDone();
        }
    }
    tick();
}

/* ========== 继续播放 ========== */
function resumeVideo() {
    // 停止并清理分支视频
    var branchVideo = $('branch-video');
    branchVideo.pause();
    branchVideo.src = '';
    $('branch-video-wrap').style.display = 'none';

    // 隐藏 AI 配图
    $('ai-image').style.display = 'none';
    $('ai-image-img').src = '';

    // 关闭弹窗，继续主视频
    $('branch-modal').classList.remove('active');
    var video = $('video-player');
    video.play();
    log('继续播放', 'info');
}
