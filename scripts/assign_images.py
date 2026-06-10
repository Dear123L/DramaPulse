import pymysql, random

conn = pymysql.connect(host='localhost', port=3306, user='root', password='root', database='drama_pulse')
cur = conn.cursor(pymysql.cursors.DictCursor)

# 9张预生成图片池
image_pool = [
    '/assets/ep67/hl5_branchA_1781094085.png',
    '/assets/ep67/hl9_branchA.png',
    '/assets/ep67/hl9_branchB.png',
    '/assets/ep67/hl9_branchC.png',
    '/assets/ep67/hl17_branchA.png',
    '/assets/ep67/hl17_branchB.png',
    '/assets/ep67/hl17_branchC.png',
    '/assets/ep67/hl23_branchA.png',
    '/assets/ep67/hl23_branchB.png',
    '/assets/ep67/hl23_branchC.png',
]

# 找出 media_path 为空且 result_type='text' 的记录
cur.execute(
    "SELECT id, highlight_id, branch_id FROM branch_results WHERE (media_path IS NULL OR media_path='') AND result_type='text'"
)
empty_rows = cur.fetchall()
print(f'需要补图的记录数: {len(empty_rows)}')
for r in empty_rows:
    print(f"  id={r['id']} hl={r['highlight_id']} branch={r['branch_id']}")

# 随机分配
random.shuffle(image_pool)
for i, row in enumerate(empty_rows):
    assigned_img = image_pool[i % len(image_pool)]
    cur.execute(
        "UPDATE branch_results SET media_path=%s, result_type='image' WHERE id=%s",
        (assigned_img, row['id'])
    )
    print(f"  更新 id={row['id']} -> {assigned_img}")

conn.commit()

# 验证结果
cur.execute('SELECT id, highlight_id, branch_id, result_type, media_path FROM branch_results ORDER BY highlight_id, branch_id')
rows = cur.fetchall()
print('\n更新后所有记录:')
for r in rows:
    print(f"  id={r['id']} hl={r['highlight_id']} branch={r['branch_id']} type={r['result_type']} img={r['media_path']}")

conn.close()
print('\n完成！')
