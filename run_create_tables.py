"""
run_create_tables.py
读取 create_tables.sql 并在 MySQL (root/root @ localhost:3306) 上执行
"""
import pymysql
import re

SQL_FILE = "create_tables.sql"
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "charset": "utf8mb4",
}

def read_sql_statements(filepath):
    """读取SQL文件，返回语句列表（正确处理括号嵌套）"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("--"):
            continue
        lines.append(line)

    full_text = " ".join(lines)
    stmts = []
    buf = ""
    paren = 0
    i = 0
    while i < len(full_text):
        ch = full_text[i]
        buf += ch
        if ch == "(":
            paren += 1
        elif ch == ")":
            paren -= 1
        elif ch == ";" and paren == 0:
            stmts.append(buf.strip())
            buf = ""
        i += 1
    return stmts

def main():
    stmts = read_sql_statements(SQL_FILE)
    print(f"解析到 {len(stmts)} 条SQL语句，开始执行...\n")

    # 第一阶段：建库 + 建表（不含 INSERT）
    conn = pymysql.connect(**DB_CONFIG, autocommit=True)
    cursor = conn.cursor()
    ddl_stmts = [s for s in stmts if not re.match(r"^\s*INSERT", s, re.IGNORECASE)]
    dml_stmts = [s for s in stmts if re.match(r"^\s*INSERT", s, re.IGNORECASE)]

    for i, stmt in enumerate(ddl_stmts):
        preview = stmt[:80].replace("\n", " ")
        try:
            cursor.execute(stmt)
            print(f"  [{i+1}/{len(ddl_stmts)}] OK  {preview}...")
        except Exception as e:
            err = str(e)
            # 忽略"已存在"类的可接受错误
            if any(k in err.upper() for k in ["ALREADY EXISTS", "42S01", "42S02"]):
                print(f"  [{i+1}/{len(ddl_stmts)}] SKIP (已存在) {preview}...")
            else:
                print(f"  [{i+1}/{len(ddl_stmts)}] ERR  {err}")
                print(f"       SQL: {preview}")

    # 验证表已创建
    cursor.execute("SHOW TABLES FROM drama_pulse")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"\n建表完成，共 {len(tables)} 张表: {tables}")

    # 第二阶段：插入示例数据
    for stmt in dml_stmts:
        preview = stmt[:80].replace("\n", " ")
        try:
            cursor.execute(stmt)
            print(f"  INSERT OK: {preview}...")
        except Exception as e:
            if "Duplicate" in str(e) or "1062" in str(e):
                print(f"  INSERT SKIP (已存在): {preview}...")
            else:
                print(f"  INSERT ERR: {e}")

    # 最终验证
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM drama_pulse.{t}")
        cnt = cursor.fetchone()[0]
        print(f"  drama_pulse.{t}: {cnt} 行")

    cursor.close()
    conn.close()
    print("\n所有操作完成！")

if __name__ == "__main__":
    main()
