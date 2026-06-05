"""
list_highlights.py
查看第67集所有高光点，用于选择要生成图片/视频的代表性分支
"""
import pymysql
import json
import config

conn = pymysql.connect(
    host=config.MYSQL_HOST,
    port=config.MYSQL_PORT,
    user=config.MYSQL_USER,
    password=config.MYSQL_PASSWORD,
    database=config.MYSQL_DATABASE,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()
cur.execute('SELECT id, timestamp, scene_desc, action_desc, emotion, branch_options, show_branch FROM highlights WHERE episode_id=1 ORDER BY timestamp')
rows = cur.fetchall()

print("=" * 80)
print("第67集 高光点列表（含分支选项）")
print("=" * 80)

for r in rows:
    opts = r.get('branch_options') or '[]'
    if isinstance(opts, str):
        try:
            opts = json.loads(opts)
        except Exception:
            opts = []
    show = "是" if r.get('show_branch') else "否"
    ts = r['timestamp']
    mm = ts // 60
    ss = ts % 60
    print(f"\nHL#{r['id']:2d}  @ {mm:02d}:{ss:02d} ({ts}s)  是否分支:{show}")
    print(f"  场景: {r.get('scene_desc','')[:70]}")
    print(f"  动作: {r.get('action_desc','')[:70]}")
    print(f"  情绪: {r.get('emotion','')}")
    if opts:
        for o in opts:
            print(f"  选项{o.get('id','?')}: {o.get('text','')}")

print("\n" + "=" * 80)
print("建议选作 AI 配图/预渲染视频 的高光点：")
print("  1. HL#17  @ 04:27  → 第一个剧情分支，用户第一次做选择，最具代表性")
print("  2. HL#?   → 选一个情绪最强烈的（恐惧/反转类）")
print("  3. HL#?   → 选一个视觉特效最丰富的（有粒子+视觉特效的）")
print("=" * 80)

conn.close()
