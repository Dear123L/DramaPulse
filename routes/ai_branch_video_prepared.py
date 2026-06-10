"""
ai_branch_video_prepared.py
方案C：预渲染视频分支（离线生成，演示用）

【工作流程】
1. 提前用 AI 视频工具（可灵 / Runway / Pika）生成短视频片段
2. 把视频文件按命名规则放到 frontend/branch_media/ep{集数}/ 目录
3. 在 branch_results 表中插入记录，result_type='video'，media_path 指向视频文件
4. 用户选分支时，后端直接返回缓存的视频路径，前端播放

【视频文件命名规则】
  frontend/branch_media/ep67/hl{highlight_id}_branch{branch_id}.mp4
  例：hl17_branchA.mp4  → 高光点#17 的 A 分支视频

【数据库准备 SQL 示例】
  INSERT INTO branch_results
    (highlight_id, episode_id, branch_id, branch_text, ai_response, media_path, result_type, token_usage)
  VALUES
    (17, 1, 'A', '探查左侧暗道', '你举起火把走向左侧...', 'branch_media/ep67/hl17_branchA.mp4', 'video', 0),
    (17, 1, 'B', '原路返回',     '你们决定退回安全地带...', 'branch_media/ep67/hl17_branchB.mp4', 'video', 0),
    (17, 1, 'C', '在岔口做标记', '你用碎瓷片在石壁上刻下标记...', 'branch_media/ep67/hl17_branchC.mp4', 'video', 0);

【前端对接】
  前端 app.js 里 onBranchSelected() 判断 data.result_type：
    - 'text'  → 显示文字
    - 'image' → 显示图片 + 文字
    - 'video' → 暂停主视频，播放分支视频，播完切回主视频
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import database

router = APIRouter(prefix="/ai", tags=["ai-video-prepared"])

# 前端 branch_media 目录（相对于 backend/）
FRONTEND_MEDIA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "branch_media"
)
os.makedirs(FRONTEND_MEDIA_DIR, exist_ok=True)

# 分支视频存放目录（按集数分子目录）
# 例：frontend/branch_media/ep67/hl17_branchA.mp4
VIDEO_DIR = FRONTEND_MEDIA_DIR


class BranchVideoRequest(BaseModel):
    episode_no:   int    = 67
    highlight_id:  int
    branch_id:     str    # A / B / C
    branch_text:   str    = ""
    context:       str    = ""


# ============================
# API 路由
# ============================

@router.post("/branch-video", summary="获取预渲染分支视频（方案C）")
def get_prepared_branch_video(req: BranchVideoRequest):
    """
    返回预渲染视频路径（或文字 fallback）。
    优先读 branch_results 缓存（result_type='video'），
    如果没有缓存则 fallback 到文字续写（result_type='text'）。
    """
    conn = database.get_connection()
    cur = conn.cursor()

    # 1. 查找高光点
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (req.episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {req.episode_no} 不存在")
    episode_id = episode["id"]

    # 2. 只查 video 类型的缓存；没有就 404，让前端降级
    cur.execute(
        "SELECT * FROM branch_results WHERE highlight_id=%s AND branch_id=%s AND result_type='video'",
        (req.highlight_id, req.branch_id),
    )
    cached = cur.fetchone()
    if cached:
        # 验证视频文件真的存在
        video_path = None
        if cached.get("media_path"):
            # media_path 可能是 /static/... 或相对路径
            maybe = os.path.join(
                os.path.dirname(__file__), "..", "frontend", "branch_media",
                f"ep{req.episode_no}", f"hl{req.highlight_id}_branch{req.branch_id}.mp4"
            )
            maybe = os.path.normpath(maybe)
            if os.path.isfile(maybe):
                video_path = "/static/branch_media/" + f"ep{req.episode_no}/hl{req.highlight_id}_branch{req.branch_id}.mp4"

        if video_path:
            return {
                "branch_id":   req.branch_id,
                "result_type":  "video",
                "text":        cached["ai_response"] or "",
                "media_url":    video_path,
                "cached":       True,
                "token_usage":  cached["token_usage"],
            }
        else:
            print(f"[branch-video] 缓存记录存在但视频文件不存在，返回404让前端降级")


    # 3. 无视频缓存或视频文件不存在 → 404，让前端降级到 /ai/branch-with-image
    raise HTTPException(
        status_code=404,
        detail=f"高光点 {req.highlight_id} 分支 {req.branch_id} 尚无预渲染视频，请让前端降级"
    )


@router.get("/branch-video/{episode_no}/{highlight_id}/{branch_id}", tags=["ai-video-prepared"])
def serve_branch_video(episode_no: int, highlight_id: int, branch_id: str):
    """
    直接返回分支视频文件（用于前端 <video> src）
    路径规则：/ai/branch-video/67/17/A  →  frontend/branch_media/ep67/hl17_branchA.mp4
    """
    video_path = os.path.join(
        VIDEO_DIR, f"ep{episode_no}", f"hl{highlight_id}_branch{branch_id}.mp4"
    )
    if not os.path.isfile(video_path):
        return {"error": "视频文件不存在", "path": video_path}

    return FileResponse(str(video_path), media_type="video/mp4")


# ============================
# 辅助：列出已有预渲染视频
# ============================

@router.get("/branch-video/list", summary="列出所有预渲染分支视频")
def list_prepared_videos(episode_no: int = None):
    """扫描 frontend/branch_media/ 目录，列出已有视频文件"""
    import json as _json

    result = []
    scan_dir = VIDEO_DIR
    if episode_no:
        scan_dir = os.path.join(VIDEO_DIR, f"ep{episode_no}")

    if not os.path.isdir(scan_dir):
        return {"videos": [], "message": f"目录不存在: {scan_dir}"}

    for root, dirs, files in os.walk(scan_dir):
        for fname in files:
            if fname.endswith(".mp4"):
                fpath = os.path.join(root, fname)
                # 解析文件名：hl{highlight_id}_branch{branch_id}.mp4
                rel  = os.path.relpath(fpath, VIDEO_DIR).replace("\\", "/")
                url  = f"/static/branch_media/{rel}"
                result.append({
                    "file":     fname,
                    "path":     rel,
                    "url":      url,
                    "size_mb":  round(os.path.getsize(fpath) / 1024 / 1024, 2),
                })

    return {"videos": result, "count": len(result)}
