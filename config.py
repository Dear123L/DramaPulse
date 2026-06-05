"""
config.py
DramaPulse 后台服务配置

敏感信息（API Key、数据库密码）从同目录的 .env 文件读取。
.env 已加入 .gitignore，不会被推送到 Git。
推代码时只需保留 .env.example 供他人参考。
"""
import os
from pathlib import Path

# 自动加载同目录下的 .env 文件
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.is_file():
        load_dotenv(_env_path, override=False)
except ImportError:
    pass  # 没装 python-dotenv 也能用，通过系统环境变量传入即可

# MySQL
MYSQL_HOST     = os.getenv("MYSQL_HOST",     "127.0.0.1")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER",     "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "drama_pulse")

# 豆包 AI（火山方舟，OpenAI 兼容接口）
AI_API_KEY  = os.getenv("AI_API_KEY",  "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
AI_MODEL_ID = os.getenv("AI_MODEL_ID", "")

# ============================================================
# 方案B：文生图 API Key（填入 .env 后 ai_branch_image.py 才可真正生图）
# ============================================================
# Stable Diffusion API（https://platform.stability.ai/）
STABLE_DIFFUSION_API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY", "")
# 豆包文生图（需在火山引擎开通，模型 ID 以控制台为准）
DOUBAO_IMAGE_API_KEY  = os.getenv("DOUBAO_IMAGE_API_KEY",  "")
DOUBAO_IMAGE_BASE_URL = os.getenv("DOUBAO_IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
# ============================================================

# FastAPI
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# 视频帧存储根目录
FRAMES_BASE_DIR = os.getenv("FRAMES_BASE_DIR", r"D:\AI全栈\ep67-analysis\frames")
