"""
models.py
数据表对应的 Python 字典结构（不用 ORM，直接操作字典）
用于文档说明和类型提示，实际查询返回 dict
"""

# episodes 表行结构
EpisodeRow = {
    "id": int,
    "episode_no": int,
    "title": str,
    "theme": str,
    "total_duration": int,
    "video_path": str,
    "status": str,  # pending / analyzing / done / failed
    "frame_count": int,
    "highlight_count": int,
    "created_at": str,
    "updated_at": str,
}

# highlights 表行结构
HighlightRow = {
    "id": int,
    "episode_id": int,
    "timestamp": int,
    "highlight_type": str,
    "emotion": str,
    "intensity": int,
    "scene_desc": str,
    "action_desc": str,
    "trigger_json": dict,  # JSON 字段，pymysql 自动解析
    "visual_effect": str,
    "particle_type": str,
    "haptic_pattern": str,
    "audio_cue": str,
    "show_branch": int,  # 0 或 1
    "branch_options": str,  # JSON 字符串
    "ai_prompt": str,
    "frame_file": str,
    "created_at": str,
}

# branch_results 表行结构
BranchResultRow = {
    "id": int,
    "highlight_id": int,
    "episode_id": int,
    "branch_id": str,  # A / B / C
    "branch_text": str,
    "ai_response": str,
    "prompt_sent": str,
    "token_usage": int,
    "created_at": str,
}

# API 响应包装函数
def episode_to_api(row: dict) -> dict:
    """把 DB 行转成 App 友好的 API 响应"""
    return {
        "id": row["id"],
        "episode_no": row["episode_no"],
        "title": row["title"],
        "theme": row["theme"],
        "total_duration": row["total_duration"],
        "status": row["status"],
        "highlight_count": row["highlight_count"],
    }


def highlight_to_api(row: dict) -> dict:
    """把 DB 行转成 App 友好的高光点响应"""
    import json

    trigger = row.get("trigger_json") or {}
    if isinstance(trigger, str):
        try:
            trigger = json.loads(trigger)
        except Exception:
            trigger = {}

    branch_options = row.get("branch_options") or "[]"
    if isinstance(branch_options, str):
        try:
            branch_options = json.loads(branch_options)
        except Exception:
            branch_options = []

    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "type": row["highlight_type"],
        "intensity": row["intensity"],
        "emotion": row["emotion"],
        "scene_desc": row["scene_desc"],
        "action_desc": row["action_desc"],
        "trigger": trigger,
        "visual_effect": row["visual_effect"],
        "particle_type": row["particle_type"],
        "haptic_pattern": row["haptic_pattern"],
        "audio_cue": row["audio_cue"],
        "show_branch": bool(row["show_branch"]),
        "branch_options": branch_options,
        "ai_prompt": row["ai_prompt"],
    }
