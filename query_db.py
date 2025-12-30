#!/usr/bin/env python3
import sqlite3
import sys

def query(sql):
    conn = sqlite3.connect('experiments.db')
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        if sql.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            for row in rows:
                print(row)
            print(f"\n总共 {len(rows)} 行")
        else:
            conn.commit()
            print(f"执行成功")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        conn.close()

if len(sys.argv) > 1:
    query(' '.join(sys.argv[1:]))
else:
    print("用法: python3 query_db.py 'SELECT * FROM experiments'")
