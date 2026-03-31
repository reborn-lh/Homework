"""
会议室预约系统 - RPC服务端
基于Python标准库xmlrpc.server实现
"""
import sqlite3
import os
import sys
from datetime import datetime
from xmlrpc.server import SimpleXMLRPCServer

# 强制无缓冲输出
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'meeting.db')


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建会议表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organizer_name TEXT NOT NULL,
            room_name TEXT NOT NULL,
            topic TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            participant_count INTEGER NOT NULL,
            cancelled INTEGER DEFAULT 0
        )
    ''')

    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_organizer
        ON meetings(organizer_name)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_room_time
        ON meetings(room_name, start_time, end_time)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cancelled
        ON meetings(cancelled)
    ''')

    conn.commit()
    conn.close()


def validate_time(start_time_str, end_time_str):
    """验证时间格式和逻辑"""
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")

        if end_time <= start_time:
            return False, "结束时间必须晚于开始时间"

        if start_time < datetime.now():
            return False, "开始时间不能早于当前时间"

        return True, "时间格式正确"

    except ValueError:
        return False, "时间格式不正确，请使用格式: YYYY-MM-DD HH:MM"


def has_conflict(room_name, start_time, end_time):
    """检测时间冲突"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM meetings
        WHERE room_name = ? AND cancelled = 0
        AND end_time > ? AND start_time < ?
    ''', (room_name, start_time, end_time))

    count = cursor.fetchone()[0]
    conn.close()

    return count > 0


def book_meeting(organizer_name, room_name, topic,
                 start_time, end_time, participant_count):
    """预约会议室"""
    print(f"[预约] 组织者: {organizer_name}, 会议室: {room_name}, 时间: {start_time} - {end_time}")

    # 验证时间
    valid, message = validate_time(start_time, end_time)
    if not valid:
        return {'success': False, 'message': message, 'meeting_id': 0}

    # 检测冲突
    if has_conflict(room_name, start_time, end_time):
        return {
            'success': False,
            'message': '该会议室在指定时间段已被预约',
            'meeting_id': 0
        }

    # 插入数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO meetings
            (organizer_name, room_name, topic, start_time, end_time, participant_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (organizer_name, room_name, topic,
              start_time, end_time, participant_count))

        meeting_id = cursor.lastrowid
        conn.commit()

        print(f"[预约成功] 会议ID: {meeting_id}")

        return {
            'success': True,
            'message': f'预约成功，会议ID: {meeting_id}',
            'meeting_id': meeting_id
        }

    except sqlite3.Error as e:
        conn.rollback()
        return {
            'success': False,
            'message': f'预约失败: {str(e)}',
            'meeting_id': 0
        }
    finally:
        conn.close()


def query_by_id(meeting_id):
    """根据ID查询预约"""
    print(f"[查询] 会议ID: {meeting_id}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id, organizer_name, room_name,
                   start_time, end_time, participant_count, cancelled
            FROM meetings
            WHERE id = ?
        ''', (meeting_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            print(f"[查询成功] 找到记录")
            return {
                'id': row[0],
                'organizer_name': row[1],
                'room_name': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'participant_count': row[5],
                'cancelled': bool(row[6])
            }
        else:
            print(f"[查询成功] 未找到记录")
            return None

    except Exception as e:
        print(f"[查询错误] {e}")
        conn.close()
        raise


def query_by_organizer(organizer_name):
    """根据组织者查询预约"""
    print(f"[查询] 组织者: {organizer_name}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, organizer_name, room_name, topic,
               start_time, end_time, participant_count, cancelled
        FROM meetings
        WHERE organizer_name = ? AND cancelled = 0
        ORDER BY start_time DESC
    ''', (organizer_name,))

    rows = cursor.fetchall()
    conn.close()

    meetings = []
    for row in rows:
        meetings.append({
            'id': row[0],
            'organizer_name': row[1],
            'room_name': row[2],
            'topic': row[3],
            'start_time': row[4],
            'end_time': row[5],
            'participant_count': row[6],
            'cancelled': bool(row[7])
        })

    print(f"[查询成功] 找到 {len(meetings)} 条记录")
    return meetings


def cancel_meeting(meeting_id):
    """取消预约"""
    print(f"[取消] 会议ID: {meeting_id}")

    # 检查会议是否存在
    meeting = query_by_id(meeting_id)
    if not meeting:
        return {
            'success': False,
            'message': '会议不存在'
        }

    # 检查是否已取消
    if meeting['cancelled']:
        return {
            'success': False,
            'message': '会议已被取消'
        }

    # 更新数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE meetings SET cancelled = 1
            WHERE id = ?
        ''', (meeting_id,))

        conn.commit()

        print(f"[取消成功] 会议ID: {meeting_id}")

        return {
            'success': True,
            'message': '会议已取消'
        }

    except sqlite3.Error as e:
        conn.rollback()
        return {
            'success': False,
            'message': f'取消失败: {str(e)}'
        }
    finally:
        conn.close()


def main():
    """启动RPC服务端"""

    # 初始化数据库
    print("初始化数据库...")
    init_database()
    print(f"数据库路径: {DB_PATH}")

    # 检查表结构
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"数据库中的表: {tables}")
    conn.close()
    print()

    # 创建服务器
    server = SimpleXMLRPCServer(("127.0.0.1", 8000), allow_none=True)

    # 注册函数
    server.register_function(book_meeting, "book_meeting")
    server.register_function(query_by_id, "query_by_id")
    server.register_function(query_by_organizer, "query_by_organizer")
    server.register_function(cancel_meeting, "cancel_meeting")

    # 启动信息
    print("=" * 60)
    print("会议室预约系统 - RPC服务端")
    print("=" * 60)
    print("服务地址: 127.0.0.1:8000")
    print("=" * 60)
    print("服务已启动，等待连接...")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n关闭服务...")


if __name__ == '__main__':
    main()
