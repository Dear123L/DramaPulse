"""
database.py
MySQL 连接管理 — 每次请求新建独立连接，线程安全
"""
import pymysql
from pymysql.cursors import DictCursor
import config


def get_connection() -> pymysql.Connection:
    """每次调用新建一个独立连接，调用方负责 close()"""
    return pymysql.Connection(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


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
    print(f"[DB] 数据库 {config.MYSQL_DATABASE} 就绪")
