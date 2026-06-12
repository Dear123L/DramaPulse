"""
ai_service.py
豆包 AI API 封装：剧情分支续写 + 视频帧分析
"""
import json
import base64
import time
from openai import OpenAI
import config

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.AI_API_KEY, base_url=config.AI_BASE_URL)
    return _client


def generate_branch(scene_desc: str, characters: str, emotion: str,
                   branch_text: str, branch_id: str) -> dict:
    """
    调用豆包 API 生成剧情分支续写

    Args:
        scene_desc: 当前场景描述
        characters: 角色状态
        emotion: 情绪氛围
        branch_text: 用户选择的选项文字
        branch_id: 选项 ID（A/B/C）

    Returns:
        dict: {"text": "续写内容", "ending_type": "survive"/"death", "token_usage": int}
    """
    client = _get_client()
    prompt = (
        f"你是一个沉浸式短剧互动体验的AI叙事引擎。\n\n"
        f"当前场景：{scene_desc}\n"
        f"角色状态：{characters}\n"
        f"情绪氛围：{emotion}\n\n"
        f"观众选择了「{branch_text}」（选项{branch_id}），请根据这个选择生成剧情续写。\n"
        f"要求：\n"
        f"1. 保持与原剧一致的文风（悬疑紧张的古墓探险风格）\n"
        f"2. 紧接当前情节，不要重复已知信息\n"
        f"3. 结尾留有悬念\n"
        f"4. 每个分支选项有不同的结局走向：其中只有一个选项是生路(survive)，其他都是死路(death)\n"
        f"5. 死路结局要写出危险逼近或陷入绝境的紧迫感，生路结局要写出转机或逃出生天的希望\n\n"
        f"严格按以下JSON格式返回（只返回JSON，不要其他文字）：\n"
        f'{{"text": "100字以内的沉浸式续写", "ending_type": "survive"}}\n'
        f'或\n'
        f'{{"text": "100字以内的沉浸式续写", "ending_type": "death"}}'
    )

    try:
        response = client.chat.completions.create(
            model=config.AI_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        result = json.loads(raw)
        text = result.get("text", "")
        ending_type = result.get("ending_type", "survive")
        if ending_type not in ("survive", "death"):
            ending_type = "survive"
        tokens = response.usage.total_tokens if response.usage else 0
        return {"text": text, "ending_type": ending_type, "token_usage": tokens}
    except json.JSONDecodeError:
        # JSON 解析失败，尝试从原始文本中提取
        tokens = response.usage.total_tokens if response.usage else 0
        return {"text": raw, "ending_type": "survive", "token_usage": tokens}
    except Exception as e:
        return {"text": f"[AI生成失败: {str(e)}]", "ending_type": "survive", "token_usage": 0}


def analyze_frame(img_path: str, timestamp: int, episode_info: str = "") -> dict:
    """
    调用豆包视觉API分析单帧图片

    Args:
        img_path: 图片路径
        timestamp: 时间戳（秒）
        episode_info: 剧集背景信息

    Returns:
        dict: AI 分析结果
    """
    client = _get_client()
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        f"这是一部短剧第{timestamp}秒的画面截图。{episode_info}\n"
        "请严格按以下JSON格式返回（只返回JSON）：\n"
        "{\n"
        '  "scene": "场景描述",\n'
        '  "characters": "人物描述",\n'
        '  "emotion": "情绪氛围",\n'
        '  "action": "人物动作描述",\n'
        '  "is_highlight": true或false,\n'
        '  "highlight_type": "高光类型（恐惧/悬疑/反转/惊吓/感动/冲突，非高光填null）",\n'
        '  "highlight_reason": "判断理由（非高光填null）",\n'
        '  "suggested_effect": "建议互动特效（手电光效/屏幕震动/心跳脉搏/剧情分支/音效触发 之一）",\n'
        '  "intensity": 1到10的强度评分\n'
        "}"
    )

    try:
        response = client.chat.completions.create(
            model=config.AI_MODEL_ID,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }],
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        result = json.loads(raw)
        result["timestamp"] = timestamp
        result["frame_file"] = img_path.split("/")[-1].split("\\")[-1]
        return result
    except json.JSONDecodeError:
        return {"timestamp": timestamp, "parse_error": True, "is_highlight": False, "intensity": 0}
    except Exception as e:
        return {"timestamp": timestamp, "error": str(e), "is_highlight": False, "intensity": 0}
