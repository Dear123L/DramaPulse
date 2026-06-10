"""
ai_branch_options.py
用豆包AI生成高光点的3个分支选项，更新到 highlights 表

接口：
  POST /ai/generate-branch-options   批量生成（所有无选项的高光点）
  POST /ai/generate-branch-options/{highlight_id}   单个生成
"""
import json
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database
import config
from ai_service import _get_client

router = APIRouter(prefix="/ai", tags=["ai-options"])


def _generate_options_with_ai(scene_desc: str, action_desc: str, emotion: str) -> list:
    """
    调用豆包AI，根据场景描述生成3个分支选项

    Returns:
        list: [{"id": "A", "text": "...", "consequence": "..."}, ...]
    """
    client = _get_client()

    prompt = (
        f"你是一个沉浸式短剧互动体验的AI叙事设计师。\n\n"
        f"当前场景：{scene_desc}\n"
        f"人物动作：{action_desc}\n"
        f"情绪氛围：{emotion}\n\n"
        f"请为这个关键时刻设计3个不同走向的互动选项，让观众选择如何继续剧情。\n"
        f"要求：\n"
        f"1. 选项A：大胆/冒险的选择\n"
        f"2. 选项B：谨慎/智慧的策略\n"
        f"3. 选项C：出人意料的第三条路\n"
        f"4. 每个选项必须与当前场景紧密相关，不能泛泛而谈\n"
        f"5. consequence 是选择后可能发生的后果预告（10字以内，制造悬念）\n\n"
        f"严格按以下JSON格式返回（只返回JSON数组，不要其他文字）：\n"
        f'[{{"id": "A", "text": "选项文字", "consequence": "后果预告"}}, '
        f'{{"id": "B", "text": "选项文字", "consequence": "后果预告"}}, '
        f'{{"id": "C", "text": "选项文字", "consequence": "后果预告"}}]'
    )

    try:
        response = client.chat.completions.create(
            model=config.AI_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        # 清理可能的 markdown 代码块标记
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        options = json.loads(raw)
        # 校验格式
        if not isinstance(options, list) or len(options) != 3:
            raise ValueError(f"AI返回格式不对，期望3个选项，得到: {options}")

        for i, opt in enumerate(options):
            if "id" not in opt:
                opt["id"] = chr(65 + i)  # A/B/C
            if "text" not in opt:
                opt["text"] = f"选项{chr(65+i)}"
            if "consequence" not in opt:
                opt["consequence"] = ""

        return options
    except json.JSONDecodeError as e:
        print(f"[BranchOptions] AI返回JSON解析失败: {e}, raw={raw[:200]}")
        return []
    except Exception as e:
        print(f"[BranchOptions] AI调用失败: {e}")
        return []


class GenerateOptionsRequest(BaseModel):
    """批量生成请求（可选过滤条件）"""
    episode_no: int = 67          # 剧集编号
    overwrite: bool = False      # 是否覆盖已有选项


@router.post("/generate-branch-options", summary="批量AI生成分支选项并更新数据库")
def generate_branch_options(req: GenerateOptionsRequest):
    """
    批量为高光点生成3个AI分支选项，更新到 highlights 表。

    - 默认只处理 branch_options 为空的高光点
    - overwrite=True 时覆盖已有选项
    """
    conn = database.get_connection()
    cur = conn.cursor()

    # 查找剧集
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (req.episode_no,))
    episode = cur.fetchone()
    if not episode:
        raise HTTPException(status_code=404, detail=f"剧集 {req.episode_no} 不存在")
    episode_id = episode["id"]

    # 查找高光点
    if req.overwrite:
        cur.execute(
            "SELECT id, scene_desc, action_desc, emotion, branch_options FROM highlights WHERE episode_id=%s AND show_branch=1",
            (episode_id,),
        )
    else:
        cur.execute(
            "SELECT id, scene_desc, action_desc, emotion, branch_options FROM highlights WHERE episode_id=%s AND show_branch=1 AND (branch_options IS NULL OR branch_options='[]' OR branch_options='')",
            (episode_id,),
        )

    highlights = cur.fetchall()
    if not highlights:
        return {
            "success": True,
            "message": "没有需要生成选项的高光点" + ("（所有高光点已有选项，可用 overwrite=True 覆盖）" if not req.overwrite else ""),
            "updated_count": 0,
            "results": [],
        }

    results = []
    for hl in highlights:
        hl_id = hl["id"]
        scene_desc = hl.get("scene_desc", "")
        action_desc = hl.get("action_desc", "")
        emotion = hl.get("emotion", "")

        # 调用AI生成选项
        options = _generate_options_with_ai(scene_desc, action_desc, emotion)

        if options:
            # 更新数据库
            options_json = json.dumps(options, ensure_ascii=False)
            cur.execute(
                "UPDATE highlights SET branch_options=%s WHERE id=%s",
                (options_json, hl_id),
            )
            results.append({
                "highlight_id": hl_id,
                "status": "success",
                "options": options,
            })
        else:
            results.append({
                "highlight_id": hl_id,
                "status": "failed",
                "options": [],
                "error": "AI生成失败",
            })

        # 批量调用间隔1秒，避免API限流
        if len(highlights) > 1:
            time.sleep(1)

    success_count = sum(1 for r in results if r["status"] == "success")
    return {
        "success": True,
        "message": f"处理 {len(results)} 个高光点，成功 {success_count} 个",
        "updated_count": success_count,
        "results": results,
    }


@router.post("/generate-branch-options/{highlight_id}", summary="单个高光点AI生成分支选项")
def generate_single_branch_options(highlight_id: int):
    """
    为指定高光点生成3个AI分支选项，更新到 highlights 表。
    无论如何都会覆盖该高光点的 branch_options。
    """
    conn = database.get_connection()
    cur = conn.cursor()

    # 查找高光点
    cur.execute(
        "SELECT id, scene_desc, action_desc, emotion FROM highlights WHERE id=%s",
        (highlight_id,),
    )
    hl = cur.fetchone()
    if not hl:
        raise HTTPException(status_code=404, detail=f"高光点 {highlight_id} 不存在")

    # 调用AI生成选项
    options = _generate_options_with_ai(
        hl.get("scene_desc", ""),
        hl.get("action_desc", ""),
        hl.get("emotion", ""),
    )

    if not options:
        raise HTTPException(status_code=500, detail="AI选项生成失败，请重试")

    # 更新数据库
    options_json = json.dumps(options, ensure_ascii=False)
    cur.execute(
        "UPDATE highlights SET branch_options=%s WHERE id=%s",
        (options_json, highlight_id),
    )

    return {
        "success": True,
        "highlight_id": highlight_id,
        "options": options,
    }
