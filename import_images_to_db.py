"""
import_images_to_db.py
把 multimodal_assets/ep67/ 里已有的图片文件写入 branch_results 缓存表

命名规则：hl{highlight_id}_branch{A/B/C}.png
例：hl17_branchA.png  → highlight_id=17, branch_id='A'

运行方式：
    cd <项目根目录>/backend
    python import_images_to_db.py
"""

import os
import re
import pymysql
import config

# 图片所在目录（相对于本脚本）
ASSETS_BASE = os.path.join(os.path.dirname(__file__), "multimodal_assets", "ep67")
# 前端访问的 URL 前缀（对应 main.py 里挂载的 /assets）
MEDIA_URL_PREFIX = "/assets"
EPISODE_NO = 67

def get_branch_text(cur, highlight_id, branch_id):
    """从数据库查对应的分支文字"""
    import json
    cur.execute("SELECT branch_options FROM highlights WHERE id=%s", (highlight_id,))
    row = cur.fetchone()
    if not row:
        return ""
    opts = row.get("branch_options") or "[]"
    if isinstance(opts, str):
        try:
            opts = json.loads(opts)
        except Exception:
            opts = []
    for opt in opts:
        if opt.get("id") == branch_id:
            return opt.get("text", "")
    return ""

def get_scene_desc(cur, highlight_id):
    cur.execute("SELECT scene_desc FROM highlights WHERE id=%s", (highlight_id,))
    row = cur.fetchone()
    return row["scene_desc"] if row else ""

def main():
    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    cur = conn.cursor()

    # 查 episode_id
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (EPISODE_NO,))
    ep = cur.fetchone()
    if not ep:
        print(f"[ERROR] 数据库里找不到 episode_no={EPISODE_NO}，请先导入剧集数据")
        return
    episode_id = ep["id"]

    # 遍历图片目录
    pattern = re.compile(r"hl(\d+)_branch([ABC])\.png", re.IGNORECASE)
    files = sorted(os.listdir(ASSETS_BASE))
    inserted = 0
    skipped  = 0

    for fname in files:
        m = pattern.match(fname)
        if not m:
            print(f"[SKIP] 文件名不符合命名规则，跳过：{fname}")
            continue

        hl_id     = int(m.group(1))
        branch_id = m.group(2).upper()
        img_path  = os.path.join(ASSETS_BASE, fname)

        branch_text = get_branch_text(cur, hl_id, branch_id)
        scene_desc  = get_scene_desc(cur, hl_id)
        # 前端访问路径：/assets/ep67/hl17_branchA.png
        media_path  = f"{MEDIA_URL_PREFIX}/ep{EPISODE_NO}/{fname}"

        # 写入（存在则更新 result_type 和 media_path）
        cur.execute(
            """INSERT INTO branch_results
               (highlight_id, episode_id, branch_id, branch_text,
                ai_response, media_path, result_type, prompt_sent, token_usage)
               VALUES (%s, %s, %s, %s, %s, %s, 'image', %s, 0)
               ON DUPLICATE KEY UPDATE
                 media_path=VALUES(media_path),
                 result_type='image',
                 branch_text=IF(branch_text='', VALUES(branch_text), branch_text)
            """,
            (
                hl_id,
                episode_id,
                branch_id,
                branch_text,
                f"（图片分支 {branch_id}）{scene_desc}",  # ai_response 占位，可后续替换
                media_path,
                f"image for hl{hl_id} branch{branch_id}",
            ),
        )
        print(f"[OK] hl{hl_id} branch{branch_id} → {media_path}  分支文字：{branch_text or '(空)'}")
        inserted += 1

    conn.close()
    print(f"\n完成：共处理 {inserted} 条，跳过 {skipped} 条")
    print(f"前端访问图片示例：http://localhost:8000/assets/ep{EPISODE_NO}/hl17_branchA.png")

if __name__ == "__main__":
    main()
