"""
会议室预约系统 - RPC客户端
基于Python标准库xmlrpc.client实现
"""
import xmlrpc.client
from datetime import datetime


class MeetingClient:
    """会议室预约客户端"""

    def __init__(self, server_url="http://127.0.0.1:8000/"):
        try:
            self.proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)
            # 测试连接
            self.server_url = server_url
            print("成功连接到服务端")
        except Exception as e:
            print(f"无法连接到服务端: {e}")
            self.proxy = None

    def book_meeting(self):
        """预约会议室"""
        print("\n" + "=" * 60)
        print("预约会议室")
        print("=" * 60)

        # 输入基本信息
        organizer_name = input("组织者姓名: ").strip()
        if not organizer_name:
            print("错误: 组织者姓名不能为空")
            return

        room_name = input("会议室名称: ").strip()
        if not room_name:
            print("错误: 会议室名称不能为空")
            return

        topic = input("会议主题: ").strip()
        if not topic:
            print("错误: 会议主题不能为空")
            return

        # 输入时间
        print("\n时间格式示例: 2026-04-01 09:00")
        start_time = input("开始时间: ").strip()
        end_time = input("结束时间: ").strip()

        if not start_time or not end_time:
            print("错误: 时间不能为空")
            return

        # 验证时间格式
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")

            if end_dt <= start_dt:
                print("错误: 结束时间必须晚于开始时间")
                return

            if start_dt < datetime.now():
                print("错误: 开始时间不能早于当前时间")
                return

        except ValueError:
            print("错误: 时间格式不正确，请使用格式: YYYY-MM-DD HH:MM")
            return

        # 输入参与人数
        participant_count = input("参与人数: ").strip()
        try:
            participant_count = int(participant_count)
            if participant_count <= 0:
                print("错误: 参与人数必须大于0")
                return
        except ValueError:
            print("错误: 请输入有效的数字")
            return

        # 调用RPC服务
        try:
            result = self.proxy.book_meeting(
                organizer_name, room_name, topic,
                start_time, end_time, participant_count
            )

            if result['success']:
                print(f"\n[成功] {result['message']}")
            else:
                print(f"\n[失败] {result['message']}")

        except Exception as e:
            print(f"\n[错误] RPC调用失败: {e}")

    def query_by_id(self):
        """根据ID查询预约"""
        print("\n" + "=" * 60)
        print("查询预约（按ID）")
        print("=" * 60)

        meeting_id = input("会议ID: ").strip()
        if not meeting_id:
            print("错误: 会议ID不能为空")
            return

        try:
            meeting_id = int(meeting_id)
        except ValueError:
            print("错误: 请输入有效的数字")
            return

        # 调用RPC服务
        try:
            meeting = self.proxy.query_by_id(meeting_id)

            if meeting:
                print("\n[查询结果]")
                self._print_meeting(meeting)
            else:
                print(f"\n[失败] 未找到会议ID为 {meeting_id} 的预约")

        except Exception as e:
            print(f"\n[错误] RPC调用失败: {e}")

    def query_by_organizer(self):
        """根据组织者查询预约"""
        print("\n" + "=" * 60)
        print("查询预约（按组织者）")
        print("=" * 60)

        organizer_name = input("组织者姓名: ").strip()
        if not organizer_name:
            print("错误: 组织者姓名不能为空")
            return

        # 调用RPC服务
        try:
            meetings = self.proxy.query_by_organizer(organizer_name)

            if meetings:
                print(f"\n[查询结果] 共找到 {len(meetings)} 条预约记录:\n")
                for i, meeting in enumerate(meetings, 1):
                    print(f"[{i}]")
                    self._print_meeting(meeting)
                    print()
            else:
                print(f"\n[失败] 未找到 {organizer_name} 的预约记录")

        except Exception as e:
            print(f"\n[错误] RPC调用失败: {e}")

    def cancel_meeting(self):
        """取消预约"""
        print("\n" + "=" * 60)
        print("取消预约")
        print("=" * 60)

        meeting_id = input("会议ID: ").strip()
        if not meeting_id:
            print("错误: 会议ID不能为空")
            return

        try:
            meeting_id = int(meeting_id)
        except ValueError:
            print("错误: 请输入有效的数字")
            return

        # 先查询会议信息
        try:
            meeting = self.proxy.query_by_id(meeting_id)

            if not meeting:
                print(f"\n[失败] 未找到会议ID为 {meeting_id} 的预约")
                return

            print("\n[会议信息]")
            self._print_meeting(meeting)

            # 确认取消
            confirm = input("\n确认取消此预约？(y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消操作")
                return

            # 调用RPC服务
            result = self.proxy.cancel_meeting(meeting_id)

            if result['success']:
                print(f"\n[成功] {result['message']}")
            else:
                print(f"\n[失败] {result['message']}")

        except Exception as e:
            print(f"\n[错误] RPC调用失败: {e}")

    def _print_meeting(self, meeting):
        """打印会议信息"""
        status = "已取消" if meeting['cancelled'] else "正常"
        print(f"  会议ID:      {meeting['id']}")
        print(f"  组织者:      {meeting['organizer_name']}")
        print(f"  会议室:      {meeting['room_name']}")
        print(f"  时间:        {meeting['start_time']} - {meeting['end_time']}")
        print(f"  参与人数:    {meeting['participant_count']}")
        print(f"  状态:        {status}")


def main():
    """客户端主程序"""

    # 创建客户端
    client = MeetingClient()

    if not client.proxy:
        print("\n请确保服务端已启动！")
        return

    # 打印欢迎信息
    print("=" * 60)
    print("会议室预约系统 - 客户端")
    print("=" * 60)

    # 主菜单循环
    try:
        while True:
            print("\n" + "=" * 60)
            print("请选择操作:")
            print("  1. 预约会议室")
            print("  2. 查询预约（按ID）")
            print("  3. 查询预约（按组织者）")
            print("  4. 取消预约")
            print("  0. 退出")
            print("=" * 60)

            choice = input("请输入选项: ").strip()

            if choice == '1':
                client.book_meeting()
            elif choice == '2':
                client.query_by_id()
            elif choice == '3':
                client.query_by_organizer()
            elif choice == '4':
                client.cancel_meeting()
            elif choice == '0':
                print("\n感谢使用，再见！")
                break
            else:
                print("\n[错误] 无效选项，请重新选择")

            # 暂停一下，让用户看清输出
            input("\n按Enter键继续...")

    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")


if __name__ == '__main__':
    main()
