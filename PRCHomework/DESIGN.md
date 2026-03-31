# 系统设计文档

## 1. 系统架构设计

### 1.1 架构图

```
                    ┌─────────────────┐
                    │  RPC Client     │
                    │   (CLI)        │
                    │  xmlrpc.client  │
                    └────────┬────────┘
                             │
                             │ HTTP/XML-RPC
                             │ Port: 8000
                             │
                    ┌────────▼────────┐
                    │  RPC Server     │
                    │ xmlrpc.server   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   SQLite       │
                    │  meeting.db     │
                    └─────────────────┘
```

### 1.2 技术栈说明

| 层次 | 技术选型 | 版本/说明 |
|------|---------|----------|
| 通信层 | XMLRPC | Python标准库 |
| 传输层 | HTTP | TCP/IP |
| 序列化 | XML | XML-RPC格式 |
| 数据层 | SQLite | Python标准库 |

## 2. 数据库设计

### 2.1 ER图

```
┌─────────────────────────────┐
│        meetings           │
├─────────────────────────────┤
│ id (PK)               INT │
│ organizer_name         TEXT│
│ room_name             TEXT│
│ topic                 TEXT│
│ start_time            TEXT│
│ end_time              TEXT│
│ participant_count      INT │
│ cancelled            INT  │
└─────────────────────────────┘
```

### 2.2 字段说明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 会议ID，自增主键 |
| organizer_name | TEXT | NOT NULL | 组织者姓名 |
| room_name | TEXT | NOT NULL | 会议室名称 |
| topic | TEXT | NOT NULL | 会议主题 |
| start_time | TEXT | NOT NULL | 开始时间，格式YYYY-MM-DD HH:MM |
| end_time | TEXT | NOT NULL | 结束时间，格式YYYY-MM-DD HH:MM |
| participant_count | INTEGER | NOT NULL | 参与人数 |
| cancelled | INTEGER | DEFAULT 0 | 是否取消，0=正常，1=已取消 |

### 2.3 SQL建表语句

```sql
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organizer_name TEXT NOT NULL,
    room_name TEXT NOT NULL,
    topic TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    participant_count INTEGER NOT NULL,
    cancelled INTEGER DEFAULT 0
);
```

### 2.4 索引设计

```sql
-- 提高按组织者查询的效率
CREATE INDEX IF NOT EXISTS idx_organizer ON meetings(organizer_name);

-- 提高冲突检测的效率
CREATE INDEX IF NOT EXISTS idx_room_time ON meetings(room_name, start_time, end_time);

-- 提高查询未取消会议的效率
CREATE INDEX IF NOT EXISTS idx_cancelled ON meetings(cancelled);
```

## 3. 接口设计

### 3.1 RPC接口列表

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| book_meeting | organizer_name, room_name, topic, start_time, end_time, participant_count | dict | 预约会议室 |
| query_by_id | meeting_id | dict/None | 根据ID查询 |
| query_by_organizer | organizer_name | list | 按组织者查询 |
| cancel_meeting | meeting_id | dict | 取消预约 |

### 3.2 接口详细说明

#### 3.2.1 book_meeting()

**请求参数:**
- organizer_name: string - 组织者姓名
- room_name: string - 会议室名称
- topic: string - 会议主题
- start_time: string - 开始时间 (格式: YYYY-MM-DD HH:MM)
- end_time: string - 结束时间 (格式: YYYY-MM-DD HH:MM)
- participant_count: integer - 参与人数

**返回值:**
```python
{
    'success': True/False,
    'message': '预约成功'/'失败原因',
    'meeting_id': 123
}
```

**业务逻辑:**
1. 验证时间格式
2. 检查时间冲突
3. 插入数据库
4. 返回结果

#### 3.2.2 query_by_id()

**请求参数:**
- meeting_id: integer - 会议ID

**返回值:**
成功:
```python
{
    'id': 123,
    'organizer_name': '张三',
    'room_name': 'A会议室',
    'topic': '项目讨论',
    'start_time': '2026-04-01 09:00',
    'end_time': '2026-04-01 11:00',
    'participant_count': 5,
    'cancelled': 0
}
```

失败: None

#### 3.2.3 query_by_organizer()

**请求参数:**
- organizer_name: string - 组织者姓名

**返回值:**
```python
[
    {
        'id': 1,
        'organizer_name': '张三',
        'room_name': 'A会议室',
        'topic': '项目讨论',
        'start_time': '2026-04-01 09:00',
        'end_time': '2026-04-01 11:00',
        'participant_count': 5,
        'cancelled': 0
    },
    {
        'id': 2,
        ...
    }
]
```

#### 3.2.4 cancel_meeting()

**请求参数:**
- meeting_id: integer - 会议ID

**返回值:**
```python
{
    'success': True/False,
    'message': '取消成功'/'失败原因'
}
```

**业务逻辑:**
1. 检查会议是否存在
2. 检查是否已取消
3. 更新cancelled字段为1
4. 返回结果

## 4. 核心算法设计

### 4.1 冲突检测算法

**问题:** 判断新预约是否与现有预约时间冲突

**算法:**
```python
def has_conflict(room_name, start_time, end_time):
    """
    检测时间冲突

    两个时间段 [s1, e1] 和 [s2, e2] 冲突的条件:
    s2 < e1 AND s1 < e2

    即: 新的开始时间 < 现有结束时间 AND 现有开始时间 < 新的结束时间
    """
    cursor.execute('''
        SELECT COUNT(*) FROM meetings
        WHERE room_name = ? AND cancelled = 0
        AND end_time > ? AND start_time < ?
    ''', (room_name, start_time, end_time))

    return cursor.fetchone()[0] > 0
```

**时间冲突示意图:**

```
情况1: 不冲突
现有: |-------|
新:            |-------|
s2 < e1? False ✗

情况2: 不冲突
新: |-------|
现有:           |-------|
s2 < e1? False ✗

情况3: 冲突
现有: |-------|
新:      |-------|
s2 < e1? True ✓

情况4: 冲突
现有:      |-------|
新:   |-------|
s2 < e1? True ✓
```

### 4.2 时间验证算法

```python
def validate_time(start_time_str, end_time_str):
    """验证时间格式和逻辑"""
    try:
        # 解析时间
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")

        # 检查逻辑
        if end_time <= start_time:
            return False, "结束时间必须晚于开始时间"

        if start_time < datetime.now():
            return False, "开始时间不能早于当前时间"

        return True, "时间格式正确"

    except ValueError:
        return False, "时间格式不正确，请使用格式: YYYY-MM-DD HH:MM"
```

## 5. 错误处理设计

### 5.1 服务端异常处理

```python
# 数据库异常
try:
    cursor.execute(sql, params)
    conn.commit()
except sqlite3.Error as e:
    conn.rollback()
    return {'success': False, 'message': f'数据库错误: {str(e)}'}

# 时间验证错误
if not valid:
    return {'success': False, 'message': error_message}

# 冲突检测
if has_conflict(...):
    return {'success': False, 'message': '该会议室在指定时间段已被预约'}
```

### 5.2 客户端异常处理

```python
# 连接异常
try:
    proxy = xmlrpc.client.ServerProxy(url)
except Exception as e:
    print(f"无法连接到服务端: {e}")
    return

# RPC调用异常
try:
    result = proxy.book_meeting(...)
except Exception as e:
    print(f"RPC调用失败: {e}")
    return
```

## 6. 安全性考虑

### 6.1 SQL注入防护

- 使用参数化查询（?占位符）
- 不拼接SQL字符串

### 6.2 输入验证

- 时间格式验证
- 数值范围验证
- 长度限制

### 6.3 并发控制

- SQLite使用文件锁
- 事务隔离级别

## 7. 性能优化

### 7.1 索引优化

- 组织者姓名索引
- 会议室+时间索引
- 状态字段索引

### 7.2 查询优化

- 只查询必要字段
- 使用WHERE条件过滤
- 分页查询（数据量大时）

## 8. 扩展性设计

### 8.1 功能扩展点

1. 用户认证
2. 权限管理
3. 会议室容量验证
4. 定时预约
5. 重复预约

### 8.2 架构扩展

1. 从单机扩展为分布式
2. 引入消息队列
3. 添加缓存层
4. 监控和日志

---

**设计完成，准备实施！**
