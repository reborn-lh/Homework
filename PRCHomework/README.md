# RPC会议室预约管理系统

基于Python XMLRPC实现的会议室预约系统，采用客户端-服务端架构。

## 功能

- 预约会议室
- 查询预约（按ID）
- 查询预约（按组织者）
- 取消预约
- 自动冲突检测

## 技术栈

| 组件 | 技术方案 |
|------|---------|
| RPC框架 | XMLRPC (Python标准库) |
| 数据库 | SQLite (Python标准库) |
| 客户端 | 命令行(CLI) |

## 数据模型

### meetings表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| organizer_name | TEXT | 组织者姓名 |
| room_name | TEXT | 会议室名称 |
| start_time | TEXT | 开始时间 |
| end_time | TEXT | 结束时间 |
| participant_count | INTEGER | 参与人数 |
| cancelled | INTEGER | 是否取消(0/1) |

## 运行

### 启动服务端

```bash
py server.py
```

或双击 `start_server.bat`

### 启动客户端

```bash
py client.py
```

或双击 `start_client.bat`

## 使用说明

1. 运行服务端，等待客户端连接
2. 运行客户端，选择操作：
   - 1: 预约会议室
   - 2: 查询预约（按ID）
   - 3: 查询预约（按组织者）
   - 4: 取消预约
   - 0: 退出

## 时间格式

使用格式：`YYYY-MM-DD HH:MM`

示例：`2026-04-01 09:00`

## 冲突检测

系统自动检测时间冲突，同一会议室在同一时间段只能有一个预约。

冲突判定规则：`end_time > 新开始时间 AND start_time < 新结束时间`
