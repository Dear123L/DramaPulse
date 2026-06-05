"""
routes/analyze.py
视频分析接口：上传/指定视频路径，触发离线分析
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import database
from analyzer import analyze_episode

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    episode_no: int
    title: str
    theme: str = "古墓探险"
    video_path: str = ""  # 本地文件路径（比赛阶段直接传路径）
    episode_info: str = ""  # 给 AI 的剧集背景


class AnalyzeResponse(BaseModel):
    episode_id: int
    episode_no: int
    frame_count: int
    highlight_count: int
    status: str
    message: str


@router.post("", summary="触发视频分析（同步，分析需要几分钟）")
def start_analysis(req: AnalyzeRequest):
    """
    触发一集的完整分析流程：
    1. 提取关键帧
    2. 调用豆包视觉AI逐帧分析
    3. 生成互动配置并存入MySQL

    注意：此接口为同步阻塞，分析一集约需2-5分钟
    """
    if not req.video_path:
        raise HTTPException(status_code=400, detail="请提供 video_path")

    import os
    if not os.path.exists(req.video_path):
        raise HTTPException(status_code=400, detail=f"视频文件不存在: {req.video_path}")

    try:
        result = analyze_episode(
            video_path=req.video_path,
            episode_no=req.episode_no,
            title=req.title,
            theme=req.theme,
            episode_info=req.episode_info,
        )
        return {
            **result,
            "message": f"分析完成，共识别 {result['highlight_count']} 个高光点",
        }
    except Exception as e:
        # 更新状态为 failed
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE episodes SET status='failed' WHERE episode_no=%s",
            (req.episode_no,),
        )
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/async", summary="触发视频分析（异步，立即返回任务ID）")
def start_analysis_async(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    异步版本：立即返回，后台执行分析。
    App 可通过轮询 GET /episodes/{episode_no} 查看状态。
    """
    if not req.video_path:
        raise HTTPException(status_code=400, detail="请提供 video_path")

    import os
    if not os.path.exists(req.video_path):
        raise HTTPException(status_code=400, detail=f"视频文件不存在: {req.video_path}")

    # 先在 DB 中创建记录
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO episodes (episode_no, title, theme, video_path, status) VALUES (%s, %s, %s, %s, 'analyzing') "
        "ON DUPLICATE KEY UPDATE status='analyzing', video_path=VALUES(video_path)",
        (req.episode_no, req.title, req.theme, req.video_path),
    )

    def _run():
        try:
            analyze_episode(
                video_path=req.video_path,
                episode_no=req.episode_no,
                title=req.title,
                theme=req.theme,
                episode_info=req.episode_info,
            )
        except Exception as e:
            conn2 = database.get_connection()
            cur2 = conn2.cursor()
            cur2.execute(
                "UPDATE episodes SET status='failed' WHERE episode_no=%s",
                (req.episode_no,),
            )

    background_tasks.add_task(_run)

    return {"episode_no": req.episode_no, "status": "analyzing", "message": "分析任务已提交，请稍后查询状态"}
