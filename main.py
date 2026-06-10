"""
main.py
DramaPulse 后台服务入口
FastAPI + MySQL + 豆包AI

启动方式:
    cd <项目根目录>/backend
    python main.py

API文档:
    http://localhost:8000/docs
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from database import init_db
from routes import episodes, analyze, ai_branch, ai_branch_image, ai_branch_video_prepared

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
VIDEO_DIR    = Path(__file__).resolve().parent
ASSETS_DIR   = Path(__file__).resolve().parent / "multimodal_assets"

app = FastAPI(
    title="DramaPulse API",
    description="短剧互动激发平台后台服务 —— 基于AI的剧情高光点分析与互动配置生成",
    version="1.0.0",
)

# 跨域支持（Android App 调用需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 托管前端静态文件（JS、CSS 等）
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend-static")

# 托管 AI 生成图片（multimodal_assets/）
# 访问 URL：http://localhost:8000/assets/ep67/hl17_branchA.png
ASSETS_DIR.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# 注册路由
app.include_router(episodes.router)
app.include_router(analyze.router)
app.include_router(ai_branch.router)
app.include_router(ai_branch_image.router)           # 方案B：文生图
app.include_router(ai_branch_video_prepared.router)  # 方案C：预渲染视频


@app.get("/", tags=["health"])
def health_check():
    """健康检查"""
    return {"status": "ok", "service": "DramaPulse API", "version": "1.0.0"}


@app.get("/player", response_class=HTMLResponse, tags=["frontend"])
def serve_player():
    """返回前端验证页面（从 http://localhost:8000/player 访问）"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path), media_type="text/html")
    return HTMLResponse("<h1>frontend/index.html not found</h1>", status_code=404)


@app.get("/video/stream", tags=["frontend"])
def serve_video():
    """提供第67集视频文件流。
    查找顺序：
    1. backend/ 目录内（和 main.py 同级）
    2. backend/ 的上级目录（兼容本地开发时视频放在 ep67-analysis/ 根目录的情况）
    """
    search_dirs = [VIDEO_DIR, VIDEO_DIR.parent]
    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.suffix.lower() == ".mp4" and "67" in f.stem:
                return FileResponse(str(f), media_type="video/mp4")
    return {"error": "video not found, please place 第67集.mp4 in backend/ directory"}


@app.get("/api/summary", tags=["health"])
def api_summary():
    """API 摘要：返回所有可用接口列表"""
    return {
        "endpoints": [
            {"method": "GET", "path": "/", "desc": "健康检查"},
            {"method": "GET", "path": "/episodes", "desc": "获取所有剧集列表"},
            {"method": "GET", "path": "/episodes/{episode_no}", "desc": "获取单集信息"},
            {"method": "GET", "path": "/episodes/{episode_no}/highlights", "desc": "获取某集高光点配置（App核心接口）"},
            {"method": "GET", "path": "/episodes/{episode_no}/highlights/{id}", "desc": "获取单个高光点"},
            {"method": "POST", "path": "/analyze", "desc": "触发视频分析（同步）"},
            {"method": "POST", "path": "/analyze/async", "desc": "触发视频分析（异步）"},
            {"method": "POST", "path": "/ai/branch", "desc": "AI生成剧情分支续写"},
        ]
    }


if __name__ == "__main__":
    import config
    uvicorn.run(
        "main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True,
    )
