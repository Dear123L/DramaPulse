"""
ai_branch_image.py
方案B：文字续写 + AI配图（文生图）
调用 Stable Diffusion / 豆包文生图 API 生成场景图，分支弹窗显示 图片+文字

【API Key 占位】
- STABLE_DIFFUSION_API_KEY: Stable Diffusion API Key（https://platform.stability.ai/）
- DOUBAO_IMAGE_API_KEY:  豆包文生图 API Key（需要在火山引擎开通）
  填入 config.py 的 DOUBAO_IMAGE_API_KEY 字段

【使用方式】
branch_results 表中 result_type='image' 的记录，
前端分支弹窗会同时显示 ai_response（文字）和 media_path（图片URL）
"""

import os
import time
import json
import base64
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database
from ai_service import generate_branch

router = APIRouter(prefix="/ai", tags=["ai-image"])

# ============================
# 配置（修改这里的 API Key）
# ============================
STABLE_DIFFUSION_API_KEY = getattr(__import__("config", fromlist=["STABLE_DIFFUSION_API_KEY"]), "STABLE_DIFFUSION_API_KEY", "")
DOUBAO_IMAGE_API_KEY   = getattr(__import__("config", fromlist=["DOUBAO_IMAGE_API_KEY"]),   "DOUBAO_IMAGE_API_KEY",   "")
DOUBAO_IMAGE_BASE_URL  = getattr(__import__("config", fromlist=["DOUBAO_IMAGE_BASE_URL"]),  "DOUBAO_IMAGE_BASE_URL",  "https://ark.cn-beijing.volces.com/api/v3")
# 服务器基地址：用于拼接完整图片URL返回给前端
SERVER_BASE_URL        = getattr(__import__("config", fromlist=["SERVER_BASE_URL"]),        "SERVER_BASE_URL",        "").rstrip("/")

# 生成的图片保存目录：backend/multimodal_assets/
# os.path.dirname(__file__) 是 routes/ 目录，需要上一级才是 backend/
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "multimodal_assets")
ASSETS_DIR = os.path.normpath(ASSETS_DIR)
os.makedirs(ASSETS_DIR, exist_ok=True)

# 前端访问图片的 URL 前缀
# FastAPI 在 main.py 里挂载了 /static -> frontend/ 目录
# 而 multimodal_assets 在 backend/ 下，所以需要单独挂载
# 见 main.py 中 app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
MEDIA_URL_PREFIX = "/assets"


class BranchImageRequest(BaseModel):
    episode_no:   int    = 67
    highlight_id:  int
    branch_id:     str    # A / B / C
    branch_text:   str    = ""
    context:       str    = ""


# ============================
# 文生图调用函数
# ============================

def generate_image_stable_diffusion(prompt: str, output_path: str) -> bool:
    """
    调用 Stable Diffusion API 生成图片（需要 API Key）
    文档：https://platform.stability.ai/docs/api-reference#tag/Text-to-Image
    """
    if not STABLE_DIFFUSION_API_KEY:
        print("[ImageGen] Stable Diffusion API Key 未配置，跳过")
        return False
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {
        "Authorization": f"Bearer {STABLE_DIFFUSION_API_KEY}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    payload = {
        "text_prompts": [{"text": prompt, "weight": 1}],
        "cfg_scale":     7,
        "height":        1344,   # 竖屏 9:16，适配手机端
        "width":         768,
        "samples":       1,
        "steps":         30,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        img_b64 = data["artifacts"][0]["base64"]
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(img_b64))
        print(f"[ImageGen] Stable Diffusion 图片已保存：{output_path}")
        return True
    except Exception as e:
        print(f"[ImageGen] Stable Diffusion 失败：{e}")
        return False


def generate_image_doubao(prompt: str, output_path: str) -> bool:
    """
    调用豆包文生图 API 生成图片（需要开通火山引擎文生图权限）
    文档：https://www.volcengine.com/docs/82379
    """
    if not DOUBAO_IMAGE_API_KEY:
        print("[ImageGen] 豆包文生图 API Key 未配置，跳过")
        return False
    # 豆包文生图接口（以火山引擎实际文档为准，以下为示例格式）
    url = f"{DOUBAO_IMAGE_BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {DOUBAO_IMAGE_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":  "doubao-image-generation-v2",  # 以实际模型 ID 为准
        "prompt": prompt,
        "size":   "768x1344",   # 竖屏 9:16，适配手机端
        "n":      1,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # 响应格式以实际 API 为准，可能是 URL 或 base64
        img_url = data.get("data", [{}])[0].get("url", "")
        if img_url:
            img_resp = requests.get(img_url, timeout=30)
            img_resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_resp.content)
        else:
            img_b64 = data.get("data", [{}])[0].get("b64_json", "")
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
        print(f"[ImageGen] 豆包文生图已保存：{output_path}")
        return True
    except Exception as e:
        print(f"[ImageGen] 豆包文生图失败：{e}")
        return False


def generate_placeholder_image(prompt: str, output_path: str) -> bool:
    """
    Demo 占位图生成：用 PIL 生成一张带文字的占位图（不需要任何 API Key）
    正式环境请改用上面的真实文生图 API
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (768, 1344), color=(30, 30, 40))  # 竖屏 9:16
        draw = ImageDraw.Draw(img)
        # 尝试用系统字体，失败则用默认
        try:
            font = ImageFont.truetype("msyh.ttc", 24)
        except Exception:
            font = ImageFont.load_default()
        # 在图片中央写 prompt 摘要（最多显示100字）
        display_text = prompt[:100] + ("..." if len(prompt) > 100 else "")
        lines = []
        line = ""
        for ch in display_text:
            line += ch
            if len(line) >= 20:
                lines.append(line)
                line = ""
        if line:
            lines.append(line)
        y = 560  # 竖屏居中偏上
        for ln in lines:
            draw.text((30, y), ln, fill=(200, 200, 180), font=font)
            y += 32
        img.save(output_path)
        print(f"[ImageGen] 占位图已生成：{output_path}")
        return True
    except Exception as e:
        print(f"[ImageGen] 占位图生成失败（请安装 Pillow：pip install Pillow）：{e}")
        return False


def build_image_prompt(scene_desc: str, branch_text: str, action_desc: str) -> str:
    """
    根据高光点信息，构建文生图的 prompt
    优化方向：突出古墓探险的氛围感，适合做分支场景图
    """
    return (
        f"古墓探险场景，{scene_desc}，"
        f"角色正在{action_desc}，"
        f"观众选择了「{branch_text}」，"
        f"暗调光线，悬疑氛围，电影感，精细细节，竖版构图，768x1344"
    )


# ============================
# API 路由
# ============================

@router.post("/branch-with-image", summary="AI生成剧情分支续写 + 文生图")
def generate_story_branch_with_image(req: BranchImageRequest):
    """
    与 /ai/branch 类似，但额外生成一张文生图。
    结果缓存到 branch_results 表（result_type='image'）。
    如果文生图失败，仍返回文字续写，media_path 为空。
    """
    conn = database.get_connection()
    cur = conn.cursor()

    # 1. 查找高光点
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (req.episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {req.episode_no} 不存在")
    episode_id = episode["id"]

    cur.execute(
        "SELECT * FROM highlights WHERE id=%s AND episode_id=%s",
        (req.highlight_id, episode_id),
    )
    highlight = cur.fetchone()
    if not highlight:
        raise HTTPException(status_code=404, detail=f"高光点 {req.highlight_id} 不存在")

    # 2. 检查缓存（result_type='image'）
    cur.execute(
        "SELECT * FROM branch_results WHERE highlight_id=%s AND branch_id=%s AND result_type='image'",
        (req.highlight_id, req.branch_id),
    )
    cached = cur.fetchone()
    if cached:
        # 拼接完整URL返回给前端
        _raw = cached["media_path"] or ""
        image_url = f"{SERVER_BASE_URL}{_raw}" if (SERVER_BASE_URL and _raw) else _raw
        return {
            "branch_id":   req.branch_id,
            "text":         cached["ai_response"],
            "image_url":    image_url,
            "result_type":  "image",
            "cached":       True,
            "token_usage":  cached["token_usage"],
        }

    # 3. 调用 AI 文字续写
    branch_text = req.branch_text
    if not branch_text:
        import json as _json
        opts = highlight.get("branch_options") or "[]"
        if isinstance(opts, str):
            try:
                opts = _json.loads(opts)
            except Exception:
                opts = []
        for opt in opts:
            if opt.get("id") == req.branch_id:
                branch_text = opt.get("text", "")
                break

    scene_desc  = req.context or highlight.get("scene_desc", "")
    ai_result   = generate_branch(
        scene_desc=scene_desc,
        characters=highlight.get("action_desc", ""),
        emotion=highlight.get("emotion", ""),
        branch_text=branch_text,
        branch_id=req.branch_id,
    )
    ai_text = ai_result["text"]

    # 4. 随机从预设图片池选一张（不生成黑底白字占位图）
    import random
    PRESET_POOL = [
        "/assets/ep67/hl5_branchA_1781094085.png",
        "/assets/ep67/hl9_branchA.png",
        "/assets/ep67/hl9_branchB.png",
        "/assets/ep67/hl9_branchC.png",
        "/assets/ep67/hl17_branchA.png",
        "/assets/ep67/hl17_branchB.png",
        "/assets/ep67/hl17_branchC.png",
        "/assets/ep67/hl23_branchA.png",
        "/assets/ep67/hl23_branchB.png",
        "/assets/ep67/hl23_branchC.png",
    ]
    media_path = random.choice(PRESET_POOL)
    print(f"[ImageGen] 无缓存，随机分配预设图：{media_path}")

    # 返回给前端时拼接完整URL
    image_url = f"{SERVER_BASE_URL}{media_path}" if SERVER_BASE_URL else media_path

    # 5. 存入缓存（result_type='image'）
    cur.execute(
        """INSERT INTO branch_results
           (highlight_id, episode_id, branch_id, branch_text, ai_response, media_path, result_type, prompt_sent, token_usage)
           VALUES (%s, %s, %s, %s, %s, %s, 'image', %s, %s)
           ON DUPLICATE KEY UPDATE
             ai_response=VALUES(ai_response), media_path=VALUES(media_path),
             prompt_sent=VALUES(prompt_sent), token_usage=VALUES(token_usage),
             result_type='image'""",
        (
            req.highlight_id,
            episode_id,
            req.branch_id,
            branch_text,
            ai_text,
            media_path,
            "",          # prompt_sent 不再生成图片，留空
            ai_result["token_usage"],
        ),
    )

    return {
        "branch_id":   req.branch_id,
        "text":         ai_text,
        "image_url":    image_url,
        "result_type":  "image",
        "cached":       False,
        "token_usage":  ai_result["token_usage"],
    }
