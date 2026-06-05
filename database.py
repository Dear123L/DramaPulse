"""
database.py
MySQL 连接池管理，通过 pymysql 实现
"""
import pymysql
from pymysql.cursors import DictCursor
import config

_pool = None

def get_connection() -> pymysql.Connection:
    """获取一个数据库连接（从连接池或新建）"""
    global _pool
    if _pool is None:
        _pool = pymysql.Connection(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=True,
        )
    # 每次调用检查连接是否存活
    try:
        _pool.ping(reconnect=True)
    except Exception:
        _pool = pymysql.Connection(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=True,
        )
    return _pool


def init_db():
    """启动时确保数据库存在（建库+建表）"""
    conn = pymysql.Connection(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    cur.execute(
        "CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        % config.MYSQL_DATABASE
    )
    conn.close()
    # 建表由 run_create_tables.py 处理，这里不再重复
    print(f"[DB] 数据库 {config.MYSQL_DATABASE} 就绪")
