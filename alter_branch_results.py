"""
alter_branch_results.py
给 branch_results 表添加 result_type 和 media_path 字段（如果不存在）
不会删除已有数据，安全执行。

运行方式：
    cd D:\AI全栈\ep67-analysis\backend
    python alter_branch_results.py
"""
import pymysql
import config

conn = pymysql.connect(
    host=config.MYSQL_HOST,
    port=config.MYSQL_PORT,
    user=config.MYSQL_USER,
    password=config.MYSQL_PASSWORD,
    database=config.MYSQL_DATABASE,
    charset="utf8mb4",
    autocommit=True,
)
cur = conn.cursor()

cur.execute("SHOW COLUMNS FROM branch_results")
cols = [r[0] for r in cur.fetchall()]
print("现有字段：", cols)

if "result_type" not in cols:
    cur.execute(
        "ALTER TABLE branch_results "
        "ADD COLUMN result_type VARCHAR(20) DEFAULT 'text' "
        "COMMENT '返回类型：text=纯文字 image=AI配图 video=预渲染视频' "
        "AFTER ai_response"
    )
    print("[OK] 添加 result_type 字段")
else:
    print("[SKIP] result_type 字段已存在")

if "media_path" not in cols:
    cur.execute(
        "ALTER TABLE branch_results "
        "ADD COLUMN media_path VARCHAR(500) DEFAULT '' "
        "COMMENT '多媒体文件访问路径，供前端拼接 URL 使用' "
        "AFTER result_type"
    )
    print("[OK] 添加 media_path 字段")
else:
    print("[SKIP] media_path 字段已存在")

cur.execute("SHOW COLUMNS FROM branch_results")
print("更新后字段：", [r[0] for r in cur.fetchall()])
conn.close()
print("完成")
