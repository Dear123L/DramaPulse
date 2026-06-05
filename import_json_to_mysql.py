"""
import_json_to_mysql.py
把 interaction_config_67.json 的数据导入 MySQL highlights 表
"""
import json, pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "drama_pulse",
    "charset": "utf8mb4",
    "autocommit": True,
}

CONFIG_FILE = r"D:\AI全栈\ep67-analysis\interaction_config_67.json"


def main():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    highlights = config.get("highlights", [])

    # 插入/更新 episode
    cur.execute(
        "INSERT INTO episodes (episode_no, title, theme, total_duration, status, highlight_count) "
        "VALUES (%s, %s, %s, %s, 'done', %s) "
        "ON DUPLICATE KEY UPDATE "
        "title=VALUES(title), theme=VALUES(theme), total_duration=VALUES(total_duration), "
        "status=VALUES(status), highlight_count=VALUES(highlight_count)",
        (config.get("episode", 67), config.get("title", ""),
         config.get("theme", ""), config.get("total_duration", 0), len(highlights)),
    )
    cur.execute("SELECT id FROM episodes WHERE episode_no=%s", (config.get("episode", 67),))
    row = cur.fetchone()
    episode_id = row["id"] if isinstance(row, dict) else row[0]
    print(f"episode_id={episode_id}, highlights={len(highlights)}")

    # 清旧数据
    cur.execute("DELETE FROM highlights WHERE episode_id=%s", (episode_id,))
    print(f"  已清除旧数据")

    # 插入 highlights
    for h in highlights:
        trigger_json = json.dumps(h.get("trigger", {}), ensure_ascii=False)
        branch_options = json.dumps(h.get("branch_options", []), ensure_ascii=False)
        cur.execute(
            "INSERT INTO highlights "
            "(episode_id, timestamp, highlight_type, emotion, intensity, "
            "scene_desc, action_desc, trigger_json, visual_effect, particle_type, "
            "haptic_pattern, audio_cue, show_branch, branch_options, ai_prompt, frame_file) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (episode_id, h.get("timestamp", 0), h.get("type", ""),
             h.get("emotion", ""), h.get("intensity", 0),
             h.get("scene_desc", ""), h.get("action_desc", ""),
             trigger_json, h.get("visual_effect", ""), h.get("particle_type", ""),
             h.get("haptic_pattern", ""), h.get("audio_cue", ""),
             1 if h.get("show_branch") else 0,
             branch_options, h.get("suggested_prompt", ""), h.get("frame_file", "")),
        )

    row = cur.fetchone()
    cnt = row["count"] if isinstance(row, dict) else (row[0] if row else 0)
    print(f"  导入完成: {len(highlights)} 条 highlights")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
