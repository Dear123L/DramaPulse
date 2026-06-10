"""
routes/episodes.py
剧集相关接口
"""
from fastapi import APIRouter, HTTPException
import database
from models import episode_to_api

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("", summary="获取所有剧集列表")
def list_episodes():
    """返回所有剧集（不含高光点详情）"""
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM episodes ORDER BY episode_no")
    rows = cur.fetchall()
    return [episode_to_api(r) for r in rows]


@router.get("/{episode_no}", summary="获取指定剧集信息")
def get_episode(episode_no: int):
    """返回单集信息"""
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM episodes WHERE episode_no=%s", (episode_no,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"剧集 {episode_no} 不存在")
    return episode_to_api(row)


@router.get("/{episode_no}/highlights", summary="获取某集所有高光点")
def get_highlights(episode_no: int):
    """返回某集的所有高光点配置（App 播放时调用这个接口）"""
    from models import highlight_to_api
    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM episodes WHERE episode_no=%s", (episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {episode_no} 不存在")

    cur.execute(
        "SELECT * FROM highlights WHERE episode_id=%s ORDER BY timestamp",
        (episode["id"],),
    )
    rows = cur.fetchall()

    return {
        "episode_no": episode_no,
        "title": episode["title"],
        "theme": episode["theme"],
        "total_duration": episode["total_duration"],
        "highlight_count": len(rows),
        "highlights": [highlight_to_api(r) for r in rows],
    }


@router.get("/{episode_no}/highlights/{highlight_id}", summary="获取单个高光点详情")
def get_highlight(episode_no: int, highlight_id: int):
    """返回单个高光点的完整信息"""
    from models import highlight_to_api
    conn = database.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {episode_no} 不存在")

    cur.execute("SELECT * FROM highlights WHERE id=%s AND episode_id=%s", (highlight_id, episode["id"]))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"高光点 {highlight_id} 不存在")

    return highlight_to_api(row)
