"""
api/ai_interaction.py
高光点互动类型分析接口

互动类型枚举：
  1 = 手电（画面变暗，用户摇手机照明，增强沉浸感）
  2 = 心跳（屏幕/震动随剧情节奏心跳，强化紧张情绪）
  3 = AI弹幕（根据场景生成几条简短弹幕，调动观众情绪）

仅对 show_branch=0（无分支）的高光点生效，有分支的已有分支互动。
"""

import json
from fastapi import APIRouter, HTTPException
import database
from ai_service import _get_client
import config

router = APIRouter(prefix="/ai", tags=["ai-interaction"])

# 互动类型说明
INTERACTION_LABELS = {
    1: "手电",
    2: "心跳",
    3: "AI弹幕",
}


def _analyze_interaction_type(highlight: dict) -> dict:
    """
    调用豆包AI，根据高光点信息判断最合适的互动类型，
    如果是弹幕(3)则同时生成5条弹幕。

    Returns:
        {"interaction_type": int, "danmaku": list[str]}
    """
    client = _get_client()

    scene_desc  = highlight.get("scene_desc", "")
    action_desc = highlight.get("action_desc", "")
    emotion     = highlight.get("emotion", "")
    intensity   = highlight.get("intensity", 5)

    prompt = (
        "你是一个短剧互动体验设计师。根据以下高光点信息，判断最合适的互动类型，"
        "并严格按JSON格式返回结果（只返回JSON，不要其他内容）。\n\n"
        f"场景描述：{scene_desc}\n"
        f"角色动作：{action_desc}\n"
        f"情绪氛围：{emotion}\n"
        f"强度评分：{intensity}/10\n\n"
        "互动类型说明：\n"
        "  1 = 手电：适合画面极暗、视野受阻、需要照明的场景（如漆黑的古墓、断电、黑暗中摸索）\n"
        "  2 = 心跳：适合极度紧张、恐惧、生死悬念的场景（如机关触发、怪物逼近、绝境求生）\n"
        "  3 = AI弹幕：适合关键转折、情绪爆发、反转揭秘的场景（如解开谜题、真相大白、情感冲突）\n\n"
        "要求：\n"
        "1. 选择最贴合场景氛围的一种\n"
        "2. 如果选择3（弹幕），生成5条弹幕，每条不超过15字，言简意赅，能贴合场景、调动情绪\n"
        "   弹幕风格：像真实观众的即时反应，可以是感叹、疑问、吐槽、共情\n"
        "3. 如果不是弹幕，danmaku字段返回空列表\n\n"
        "严格返回以下JSON格式：\n"
        '{"interaction_type": 1或2或3, "danmaku": ["弹幕1", "弹幕2", ...]}'
    )

    try:
        response = _get_client().chat.completions.create(
            model=config.AI_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        # 去掉可能的 ```json 包裹
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        result = json.loads(raw)
        interaction_type = int(result.get("interaction_type", 2))
        danmaku = result.get("danmaku", [])
        # 非弹幕类型强制清空
        if interaction_type != 3:
            danmaku = []
        return {"interaction_type": interaction_type, "danmaku": danmaku}
    except Exception as e:
        # 降级：默认心跳
        return {"interaction_type": 2, "danmaku": [], "error": str(e)}


# ============================
# API 路由
# ============================

@router.post(
    "/analyze-interaction/{highlight_id}",
    summary="AI分析高光点互动类型",
)
def analyze_interaction(highlight_id: int, episode_no: int = 67, force: bool = False):
    """
    对指定高光点进行互动类型分析，AI判断并写入数据库。

    - **highlight_id**: 高光点ID
    - **episode_no**: 剧集编号，默认67
    - **force**: 是否强制重新分析（默认跳过已分析的）

    互动类型：
    - 1 = 手电（画面暗→用户摇手机照明）
    - 2 = 心跳（紧张情绪→屏幕/震动心跳）
    - 3 = AI弹幕（关键场景→弹幕刷屏）
    """
    conn = database.get_connection()
    cur = conn.cursor()

    # 查集
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {episode_no} 不存在")

    # 查高光点
    cur.execute(
        "SELECT * FROM highlights WHERE id=%s AND episode_id=%s",
        (highlight_id, episode["id"]),
    )
    highlight = cur.fetchone()
    if not highlight:
        raise HTTPException(status_code=404, detail=f"高光点 {highlight_id} 不存在")

    # 已分析过且不强制重跑则直接返回缓存
    if highlight.get("interaction_type") is not None and not force:
        danmaku = highlight.get("ai_danmaku") or []
        if isinstance(danmaku, str):
            try:
                danmaku = json.loads(danmaku)
            except Exception:
                danmaku = []
        return {
            "highlight_id": highlight_id,
            "interaction_type": highlight["interaction_type"],
            "interaction_label": INTERACTION_LABELS.get(highlight["interaction_type"], "未知"),
            "danmaku": danmaku,
            "cached": True,
        }

    # 调用AI分析
    result = _analyze_interaction_type(highlight)
    interaction_type = result["interaction_type"]
    danmaku = result["danmaku"]

    # 写入数据库
    cur.execute(
        "UPDATE highlights SET interaction_type=%s, ai_danmaku=%s WHERE id=%s",
        (interaction_type, json.dumps(danmaku, ensure_ascii=False), highlight_id),
    )
    conn.commit()

    return {
        "highlight_id": highlight_id,
        "interaction_type": interaction_type,
        "interaction_label": INTERACTION_LABELS.get(interaction_type, "未知"),
        "danmaku": danmaku,
        "cached": False,
        **({"ai_error": result["error"]} if "error" in result else {}),
    }


@router.post(
    "/analyze-interaction/batch/{episode_no}",
    summary="批量分析一整集所有无分支高光点的互动类型",
)
def batch_analyze_interaction(episode_no: int, force: bool = False):
    """
    批量对一整集的所有 show_branch=0 高光点做互动类型分析。

    - **force**: True则全部重新分析，False则跳过已分析的
    """
    import time as _time

    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {episode_no} 不存在")

    # 只处理无分支的高光点
    condition = "episode_id=%s AND show_branch=0"
    if not force:
        condition += " AND interaction_type IS NULL"
    cur.execute(f"SELECT * FROM highlights WHERE {condition} ORDER BY id", (episode["id"],))
    highlights = cur.fetchall()

    if not highlights:
        return {"message": "没有需要分析的高光点", "total": 0, "results": []}

    results = []
    for hl in highlights:
        result = _analyze_interaction_type(hl)
        interaction_type = result["interaction_type"]
        danmaku = result["danmaku"]

        cur.execute(
            "UPDATE highlights SET interaction_type=%s, ai_danmaku=%s WHERE id=%s",
            (interaction_type, json.dumps(danmaku, ensure_ascii=False), hl["id"]),
        )
        conn.commit()

        results.append({
            "highlight_id": hl["id"],
            "timestamp": hl["timestamp"],
            "interaction_type": interaction_type,
            "interaction_label": INTERACTION_LABELS.get(interaction_type, "未知"),
            "danmaku_count": len(danmaku),
        })
        _time.sleep(0.5)  # 防限流

    return {
        "total": len(results),
        "results": results,
    }
