"""
routes/ai_branch.py
AI 剧情分支续写接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database
from ai_service import generate_branch

router = APIRouter(prefix="/ai", tags=["ai"])


class BranchRequest(BaseModel):
    episode_no: int = 67  # 默认第67集
    highlight_id: int
    branch_id: str  # A / B / C
    branch_text: str = ""
    context: str = ""  # 前端传的场景描述（兼容旧调用）


@router.post("/branch", summary="AI生成剧情分支续写")
def generate_story_branch(req: BranchRequest):
    """
    根据高光点上下文和用户选择的分支，调用豆包AI生成剧情续写。
    结果会缓存到 branch_results 表，相同选择不重复调用AI。
    """
    conn = database.get_connection()
    try:
        cur = conn.cursor()

        # 1. 查找高光点
        cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (req.episode_no,))
        episode = cur.fetchone()
        if not episode:
            raise HTTPException(status_code=404, detail=f"剧集 {req.episode_no} 不存在")

        cur.execute(
            "SELECT * FROM highlights WHERE id=%s AND episode_id=%s",
            (req.highlight_id, episode["id"]),
        )
        highlight = cur.fetchone()
        if not highlight:
            raise HTTPException(status_code=404, detail=f"高光点 {req.highlight_id} 不存在")

        # 2. 检查缓存
        cur.execute(
            "SELECT * FROM branch_results WHERE highlight_id=%s AND branch_id=%s",
            (req.highlight_id, req.branch_id),
        )
        cached = cur.fetchone()
        if cached:
            return {
                "branch_id": req.branch_id,
                "text": cached["ai_response"],
                "ending_type": cached.get("ending_type", "survive"),
                "cached": True,
                "token_usage": cached["token_usage"],
            }

        # 3. 调用 AI
        branch_text = req.branch_text
        if not branch_text:
            # 从高光点的 branch_options 中找
            import json
            opts = highlight.get("branch_options") or "[]"
            if isinstance(opts, str):
                try:
                    opts = json.loads(opts)
                except Exception:
                    opts = []
            for opt in opts:
                if opt.get("id") == req.branch_id:
                    branch_text = opt.get("text", "")
                    break

        # 优先用前端传的 context，否则用数据库里的 scene_desc
        scene_desc = req.context or highlight.get("scene_desc", "")
        prompt = highlight.get("ai_prompt") or ""

        result = generate_branch(
            scene_desc=scene_desc,
            characters=highlight.get("action_desc", ""),
            emotion=highlight.get("emotion", ""),
            branch_text=branch_text,
            branch_id=req.branch_id,
        )

        # 4. 存入缓存（含 ending_type）
        cur.execute(
            """INSERT INTO branch_results (highlight_id, episode_id, branch_id, branch_text, ai_response, ending_type, prompt_sent, token_usage)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                req.highlight_id,
                episode["id"],
                req.branch_id,
                branch_text,
                result["text"],
                result["ending_type"],
                prompt,
                result["token_usage"],
            ),
        )

        return {
            "branch_id": req.branch_id,
            "text": result["text"],
            "ending_type": result["ending_type"],
            "cached": False,
            "token_usage": result["token_usage"],
        }
    finally:
        conn.close()
