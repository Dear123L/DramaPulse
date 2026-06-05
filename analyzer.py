"""
analyzer.py
视频分析流水线：提取帧 → AI 分析 → 生成互动配置 → 存入 MySQL
复用现有 extract_and_analyze_ep67.py 的核心逻辑，改为通用版
"""
import os
import json
import time
from PIL import Image
import imageio
import database
from ai_service import analyze_frame

# 高光类型 → 特效映射（古墓探险主题，可按集数扩展）
DEFAULT_EFFECT_MAP = {
    "恐惧": {"effect": "heartbeat_pulse", "particle": "dark_fog", "haptic": "vibrate_pattern_heartbeat", "branch": False, "audio": "low_freq_drone"},
    "悬疑": {"effect": "flashlight_flicker", "particle": "dust_mote", "haptic": "vibrate_light", "branch": True, "audio": "creak_sound"},
    "反转": {"effect": "screen_flash", "particle": "spark_burst", "haptic": "vibrate_sharp", "branch": True, "audio": "impact_boom"},
    "惊吓": {"effect": "screen_shake", "particle": "shadow_leech", "haptic": "vibrate_sustained", "branch": False, "audio": "sudden_scare"},
    "感动": {"effect": "light_bloom", "particle": "warm_glow", "haptic": "vibrate_gentle", "branch": False, "audio": "emotional_sting"},
    "冲突": {"effect": "camera_shake", "particle": "rubble", "haptic": "vibrate_heavy", "branch": True, "audio": "crash_rumble"},
}


def extract_frames(video_path: str, output_dir: str, interval: int = 15) -> list:
    """
    从视频中提取关键帧

    Args:
        video_path: 视频文件路径
        output_dir: 帧输出目录
        interval: 采样间隔（秒），默认15秒

    Returns:
        list: 提取的时间戳列表
    """
    os.makedirs(output_dir, exist_ok=True)
    reader = imageio.get_reader(video_path)
    meta = reader.get_meta_data()
    fps = meta["fps"]
    total_seconds = int(meta["duration"])

    timestamps = list(range(0, total_seconds, interval))
    # 最后30秒密集采样
    for t in range(max(0, total_seconds - 30), total_seconds + 1, 5):
        if t not in timestamps:
            timestamps.append(t)
    timestamps = sorted(set(t for t in timestamps if t <= total_seconds))

    for ts in timestamps:
        fname = f"t{ts:04d}s.jpg"
        fpath = os.path.join(output_dir, fname)
        if os.path.exists(fpath):
            continue
        try:
            frame_idx = int(ts * fps)
            frame = reader.get_data(frame_idx)
            img = Image.fromarray(frame)
            w, h = img.size
            ratio = 360 / w
            img = img.resize((360, int(h * ratio)), Image.LANCZOS)
            img.save(fpath, "JPEG", quality=85)
        except Exception:
            pass
        time.sleep(0.1)

    reader.close()
    return timestamps


def analyze_episode(video_path: str, episode_no: int, title: str,
                    theme: str = "古墓探险", episode_info: str = "") -> dict:
    """
    完整分析一集：提取帧 → AI分析 → 存入MySQL

    Args:
        video_path: 视频文件路径
        episode_no: 集数
        title: 标题
        theme: 主题
        episode_info: 给 AI 的剧集背景描述

    Returns:
        dict: 分析结果摘要 {"episode_id": int, "frame_count": int, "highlight_count": int}
    """
    import config
    frames_dir = os.path.join(config.FRAMES_BASE_DIR, f"ep{episode_no}")
    conn = database.get_connection()
    cur = conn.cursor()

    # 1. 更新状态为 analyzing
    cur.execute(
        "INSERT INTO episodes (episode_no, title, theme, video_path, status) VALUES (%s, %s, %s, %s, 'analyzing') "
        "ON DUPLICATE KEY UPDATE status='analyzing', video_path=VALUES(video_path)",
        (episode_no, title, theme, video_path),
    )
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (episode_no,))
    episode_id = cur.fetchone()["id"]

    # 2. 提取帧
    timestamps = extract_frames(video_path, frames_dir)
    frame_count = len(timestamps)
    cur.execute("UPDATE episodes SET frame_count=%s WHERE id=%s", (frame_count, episode_id))

    # 3. AI 分析每帧
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])
    results = []
    for i, fname in enumerate(frame_files):
        ts = int(fname[1:5])
        img_path = os.path.join(frames_dir, fname)
        result = analyze_frame(img_path, ts, episode_info)
        results.append(result)
        if i < len(frame_files) - 1:
            time.sleep(1.5)

    # 4. 筛选高光点并写入 highlights 表
    highlights = [r for r in results if r.get("is_highlight") and "error" not in r and "parse_error" not in r]
    highlight_count = 0

    for h in highlights:
        hl_type = h.get("highlight_type") or "悬疑"
        eff = DEFAULT_EFFECT_MAP.get(hl_type, DEFAULT_EFFECT_MAP["悬疑"])
        trigger = {
            "auto": True,
            "gesture": "shake" if hl_type in ["恐惧", "惊吓"] else "double_tap",
            "window_ms": 4000,
            "cooldown_ms": 10000,
        }
        branch_opts = (
            [
                {"id": "A", "text": "探查前方暗道", "consequence": "触发隐藏机关"},
                {"id": "B", "text": "原地等待观察", "consequence": "发现墙上有暗号"},
                {"id": "C", "text": "回头撤退", "consequence": "退路已被封死"},
            ]
            if eff["branch"]
            else []
        )
        cur.execute(
            """INSERT INTO highlights
               (episode_id, timestamp, highlight_type, emotion, intensity,
                scene_desc, action_desc, trigger_json, visual_effect, particle_type,
                haptic_pattern, audio_cue, show_branch, branch_options, ai_prompt, frame_file)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                episode_id,
                h["timestamp"],
                hl_type,
                h.get("emotion", ""),
                h.get("intensity", 5),
                h.get("scene", ""),
                h.get("action", ""),
                json.dumps(trigger, ensure_ascii=False),
                eff["effect"],
                eff["particle"],
                eff["haptic"],
                eff["audio"],
                1 if eff["branch"] else 0,
                json.dumps(branch_opts, ensure_ascii=False),
                f"场景:{h.get('scene','')}\n角色状态:{h.get('characters','')}\n情绪氛围:{h.get('emotion','')}\n请为观众生成一段沉浸式引导文字",
                h.get("frame_file", ""),
            ),
        )
        highlight_count += 1

    # 5. 更新 episode 状态
    cur.execute(
        "UPDATE episodes SET status='done', highlight_count=%s WHERE id=%s",
        (highlight_count, episode_id),
    )

    return {
        "episode_id": episode_id,
        "episode_no": episode_no,
        "frame_count": frame_count,
        "highlight_count": highlight_count,
        "status": "done",
    }
