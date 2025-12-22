#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
超星学习通交互式运行器
实现手动登录 -> 课程选择 -> 答题模式选择 -> 任务执行 -> 重新选择课程的循环流程
"""

import sys
import os
import configparser
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.base import Chaoxing, Account
from api.answer import Tiku
from api.exceptions import LoginError
from api.logger import logger
from main import init_chaoxing, process_course, load_config_from_file, build_config_from_args, parse_args


class InteractiveRunner:
    def __init__(self):
        self.chaoxing = None
        self.account = None
        self.tiku = None
        self.all_courses = []
        self.common_config = {}
        self.tiku_config = {}
        self.notification_config = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        if os.path.exists(config_path):
            try:
                self.common_config, self.tiku_config, self.notification_config = load_config_from_file(config_path)
                print("✅ 配置文件加载成功")
                if self.tiku_config.get('provider'):
                    print(f"📖 题库: {self.tiku_config.get('provider')}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}，将使用默认设置")
        else:
            print("⚠️ 未找到配置文件 config.ini，将使用默认设置")

    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        """打印欢迎横幅"""
        print("🎮 超星学习通交互式自动化工具")
        print("=" * 50)
        print("功能：手动登录 + 课程选择 + AI答题")
        print("=" * 50)
        print()

    def manual_login(self) -> bool:
        """手动登录流程"""
        print("📝 请登录你的超星学习通账号")
        print("-" * 30)

        while True:
            username = input("请输入手机号: ").strip()
            if not username:
                print("❌ 手机号不能为空")
                continue

            if not username.isdigit() or len(username) != 11:
                print("❌ 请输入正确的11位手机号")
                continue

            break

        while True:
            password = input("请输入密码: ").strip()
            if not password:
                print("❌ 密码不能为空")
                continue
            if len(password) < 6:
                print("❌ 密码长度至少6位")
                continue
            break

        print("\n🔄 正在登录...")

        try:
            # 创建账号对象
            self.account = Account(username, password)

            # 初始化题库（使用配置文件中的AI设置）
            self.tiku = Tiku()
            self.tiku.config_set(self.tiku_config)
            self.tiku = self.tiku.get_tiku_from_config()
            self.tiku.init_tiku()

            # 获取查询延迟设置
            query_delay = self.tiku_config.get("delay", 0)

            # 初始化超星实例
            self.chaoxing = Chaoxing(account=self.account, tiku=self.tiku, query_delay=query_delay)

            # 执行登录
            login_result = self.chaoxing.login(login_with_cookies=False)

            if login_result["status"]:
                print("✅ 登录成功！")
                return True
            else:
                print(f"❌ 登录失败: {login_result['msg']}")
                return False

        except LoginError as e:
            print(f"❌ 登录错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 登录出现异常: {e}")
            return False

    def load_courses(self) -> bool:
        """加载课程列表"""
        print("\n📚 正在读取课程表...")

        try:
            self.all_courses = self.chaoxing.get_course_list()

            if not self.all_courses:
                print("❌ 没有找到任何课程")
                return False

            print(f"✅ 成功读取到 {len(self.all_courses)} 门课程")
            return True

        except Exception as e:
            print(f"❌ 读取课程列表失败: {e}")
            return False

    def display_courses(self) -> List[Dict]:
        """显示课程列表并返回用户选择的课程"""
        print("\n📖 课程列表:")
        print("-" * 50)

        for i, course in enumerate(self.all_courses, 1):
            name = course.get('title', '未知课程')
            teacher = course.get('teacher', '未知教师')
            course_id = course.get('courseId', '未知ID')

            print(f"{i:2d}. {name}")
            print(f"    教师: {teacher}")
            print(f"    ID: {course_id}")
            print()

        while True:
            try:
                choice = input("请选择要完成的课程编号 (输入0退出): ").strip()

                if choice == '0':
                    return []

                choice_num = int(choice)

                if 1 <= choice_num <= len(self.all_courses):
                    selected_course = self.all_courses[choice_num - 1]
                    print(f"\n✅ 已选择课程: {selected_course.get('title', '未知课程')}")
                    return [selected_course]
                else:
                    print(f"❌ 请输入1-{len(self.all_courses)}之间的数字")

            except ValueError:
                print("❌ 请输入有效的数字")

    def select_answer_mode(self) -> Dict[str, Any]:
        """选择答题模式"""
        print("\n🤖 选择答题模式:")
        print("1. 自动提交模式 (答完题后自动提交)")
        print("2. 手动提交模式 (答完题后保存，需要手动检查后提交)")
        print()

        while True:
            choice = input("请选择 (1-2): ").strip()

            if choice == '1':
                print("✅ 已选择: 自动提交模式")
                return {"auto_submit": True}
            elif choice == '2':
                print("✅ 已选择: 手动提交模式")
                return {"auto_submit": False}
            else:
                print("❌ 请输入1或2")

    def execute_tasks(self, selected_courses: List[Dict], answer_config: Dict[str, Any]):
        """执行学习任务"""
        print(f"\n🎯 开始执行学习任务...")
        print("=" * 50)

        # 根据用户选择更新题库提交模式
        if self.tiku and not self.tiku.DISABLE:
            self.tiku.SUBMIT = answer_config.get("auto_submit", False)
            print(f"📝 答题模式: {'自动提交' if self.tiku.SUBMIT else '手动提交'}")

        # 构建任务配置
        task_config = {
            "speed": 2.0,
            "jobs": 4,
            "notopen_action": "retry"
        }

        try:
            for course in selected_courses:
                print(f"\n📚 正在学习课程: {course.get('title', '未知课程')}")
                print("-" * 30)

                # 使用原版的process_course函数处理课程
                process_course(self.chaoxing, course, task_config)

                print(f"✅ 课程 '{course.get('title', '未知课程')}' 学习完成")

            print(f"\n🎉 所有选定的课程学习任务已完成！")

        except Exception as e:
            print(f"❌ 执行任务时出现错误: {e}")
            logger.exception("任务执行异常")

    def ask_continue(self) -> bool:
        """询问是否继续选择其他课程"""
        print("\n" + "=" * 50)
        while True:
            choice = input("是否继续选择其他课程学习? (y/n): ").strip().lower()

            if choice in ['y', 'yes', '是']:
                return True
            elif choice in ['n', 'no', '否']:
                return False
            else:
                print("❌ 请输入 y(是) 或 n(否)")

    def run(self):
        """运行主循环"""
        try:
            self.clear_screen()
            self.print_banner()

            # 第一步：登录
            if not self.manual_login():
                print("\n❌ 登录失败，程序退出")
                return

            # 第二步：加载课程
            if not self.load_courses():
                print("\n❌ 加载课程失败，程序退出")
                return

            # 主循环：课程选择 -> 执行 -> 继续/退出
            while True:
                self.clear_screen()
                self.print_banner()
                print(f"👤 当前登录: {self.account.username}")
                print(f"📚 可用课程: {len(self.all_courses)} 门")
                print("=" * 50)

                # 选择课程
                selected_courses = self.display_courses()

                if not selected_courses:
                    print("👋 退出程序")
                    break

                # 选择答题模式
                answer_config = self.select_answer_mode()

                # 执行任务
                self.execute_tasks(selected_courses, answer_config)

                # 询问是否继续
                if not self.ask_continue():
                    print("\n👋 感谢使用，再见！")
                    break

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，程序退出")
        except Exception as e:
            print(f"\n❌ 程序出现异常: {e}")
            logger.exception("程序异常")


def main():
    """主入口函数"""
    runner = InteractiveRunner()
    runner.run()


if __name__ == "__main__":
    main()