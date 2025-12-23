#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
import multiprocessing
import signal
import time
import queue
import traceback
import hashlib
import functools
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import configparser
from flask_socketio import SocketIO, emit

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.base import Chaoxing, Account, StudyResult
from api.answer import Tiku
from api.exceptions import LoginError
from api.logger import logger
from main import load_config_from_file, process_course

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chaoxing-web-secret-key-2024-secure-random'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # Session 有效期 24 小时

# ============ 前置密码验证 ============
# 密码哈希（SHA256）- 原密码: 314394
ACCESS_PASSWORD_HASH = hashlib.sha256("314394".encode()).hexdigest()

def require_auth(f):
    """验证装饰器 - 保护需要密码验证的路由"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # API 请求返回 JSON 错误
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "请先完成密码验证", "auth_required": True}), 401
            # 页面请求重定向到验证页
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    return decorated_function

# 初始化 SocketIO（不指定 async_mode，让库自动选择最佳模式）
socketio = SocketIO(app, cors_allowed_origins="*")


class WebTaskManager:
    """Web 任务管理器"""
    
    def __init__(self):
        self.chaoxing: Optional[Chaoxing] = None
        self.account: Optional[Account] = None
        self.tiku: Optional[Tiku] = None
        self.all_courses: List[Dict] = []
        self.common_config: Dict = {}
        self.tiku_config: Dict = {}
        self.notification_config: Dict = {}
        self.is_logged_in: bool = False
        self.current_process: Optional[multiprocessing.Process] = None
        self.task_running: bool = False
        self.should_stop: bool = False
        self.log_queue: queue.Queue = queue.Queue()
        # 保存登录凭证用于子进程
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
        if os.path.exists(config_path):
            try:
                self.common_config, self.tiku_config, self.notification_config = load_config_from_file(config_path)
                self._emit_log("info", "配置文件加载成功")
                if self.tiku_config.get('provider'):
                    self._emit_log("info", f"题库: {self.tiku_config.get('provider')}")
            except Exception as e:
                self._emit_log("warning", f"加载配置文件失败: {e}")
        else:
            self._emit_log("warning", "未找到配置文件 config.ini")
    
    def _emit_log(self, level: str, message: str):
        """发送日志到前端"""
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        socketio.emit('log', log_entry)
        
    def _emit_progress(self, data: Dict):
        """发送进度到前端"""
        socketio.emit('progress', data)
        
    def _emit_status(self, status: str, data: Dict = None):
        """发送状态更新到前端"""
        socketio.emit('status', {"status": status, "data": data or {}})
    
    def _on_video_progress(self, data: Dict):
        """视频进度回调 - 发送到Web前端"""
        try:
            progress_type = data.get("type", "")
            name = data.get("name", "")
            duration = data.get("duration", 0)
            play_time = data.get("play_time", 0)
            percent = data.get("percent", 0)
            
            # 格式化时间显示
            def format_time(seconds):
                m, s = divmod(int(seconds), 60)
                return f"{m:02d}:{s:02d}"
            
            if progress_type == "video_start":
                self._emit_log("info", f"▶ 开始播放: {name} ({format_time(play_time)}/{format_time(duration)})")
            elif progress_type == "video_progress":
                # 构建进度条
                bar_len = 20
                filled = int(bar_len * percent / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                self._emit_log("info", f"📹 {name}: [{bar}] {percent}% ({format_time(play_time)}/{format_time(duration)})")
            elif progress_type == "video_complete":
                self._emit_log("success", f"✅ 完成: {name}")
        except Exception as e:
            pass  # 忽略进度回调错误，不影响主流程
    
    def login(self, username: str, password: str) -> Dict:
        """执行登录"""
        try:
            self._emit_log("info", f"正在登录账号: {username[:3]}****{username[-4:]}")
            
            # 保存凭证用于子进程
            self._username = username
            self._password = password
            
            # 创建账号对象
            self.account = Account(username, password)
            
            # 初始化题库
            self.tiku = Tiku()
            self.tiku.config_set(self.tiku_config)
            self.tiku = self.tiku.get_tiku_from_config()
            self.tiku.init_tiku()
            
            # 获取查询延迟设置
            query_delay = self.tiku_config.get("delay", 0)
            
            # 初始化超星实例（传入进度回调和停止检查回调）
            self.chaoxing = Chaoxing(
                account=self.account, 
                tiku=self.tiku, 
                progress_callback=self._on_video_progress,
                should_stop_callback=lambda: self.should_stop,
                query_delay=query_delay
            )
            
            # 执行登录
            login_result = self.chaoxing.login(login_with_cookies=False)
            
            if login_result["status"]:
                self.is_logged_in = True
                self._emit_log("success", "登录成功!")
                self._emit_status("logged_in", {"username": username})
                return {"success": True, "message": "登录成功"}
            else:
                self._emit_log("error", f"登录失败: {login_result['msg']}")
                return {"success": False, "message": login_result['msg']}
                
        except LoginError as e:
            self._emit_log("error", f"登录错误: {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            self._emit_log("error", f"登录异常: {e}")
            return {"success": False, "message": str(e)}
    
    def get_courses(self) -> Dict:
        """获取课程列表"""
        if not self.is_logged_in:
            return {"success": False, "message": "请先登录"}
        
        try:
            self._emit_log("info", "正在获取课程列表...")
            self.all_courses = self.chaoxing.get_course_list()
            
            if not self.all_courses:
                self._emit_log("warning", "没有找到任何课程")
                return {"success": False, "message": "没有找到任何课程"}
            
            self._emit_log("success", f"成功获取 {len(self.all_courses)} 门课程")
            
            # 格式化课程数据
            courses_data = []
            for course in self.all_courses:
                courses_data.append({
                    "courseId": course.get("courseId", ""),
                    "title": course.get("title", "未知课程"),
                    "teacher": course.get("teacher", "未知教师"),
                    "clazzId": course.get("clazzId", ""),
                    "cpi": course.get("cpi", "")
                })
            
            return {"success": True, "courses": courses_data}
            
        except Exception as e:
            self._emit_log("error", f"获取课程列表失败: {e}")
            return {"success": False, "message": str(e)}
    
    def start_task(self, course_ids: List[str], auto_submit: bool = False, speed: float = 2.0):
        """开始执行任务"""
        if not self.is_logged_in:
            return {"success": False, "message": "请先登录"}
        
        if self.task_running:
            return {"success": False, "message": "已有任务在运行中"}
        
        # 筛选选中的课程
        selected_courses = [c for c in self.all_courses if c.get("courseId") in course_ids]
        
        if not selected_courses:
            return {"success": False, "message": "请选择至少一门课程"}
        
        # 重新加载配置并初始化题库（确保使用最新的 AI 配置）
        try:
            self._load_config()
            self.tiku = Tiku()
            self.tiku.config_set(self.tiku_config)
            self.tiku = self.tiku.get_tiku_from_config()
            self.tiku.init_tiku()
            # 更新 chaoxing 实例的题库引用
            if self.chaoxing:
                self.chaoxing.tiku = self.tiku
            self._emit_log("info", f"题库已刷新: {self.tiku.name if hasattr(self.tiku, 'name') and self.tiku.name else '已禁用'}")
        except Exception as e:
            self._emit_log("warning", f"题库初始化失败: {e}，将继续执行任务")
        
        self.should_stop = False
        self.task_running = True
        
        # 创建进程间通信队列
        self.log_queue = multiprocessing.Queue()
        
        # 立即发送任务开始状态
        self._emit_status("task_started", {"total": len(selected_courses)})
        self._emit_log("info", f"开始执行 {len(selected_courses)} 门课程...")
        self._emit_log("info", f"答题模式: {'自动提交' if auto_submit else '手动保存'}")
        
        # 在子进程中执行任务（可以直接 terminate 杀死）
        self.current_process = multiprocessing.Process(
            target=run_task_in_process,
            args=(
                self._username,
                self._password,
                selected_courses,
                self.tiku_config,
                auto_submit,
                speed,
                self.log_queue  # 传递日志队列
            ),
            daemon=True
        )
        self.current_process.start()
        
        # 启动日志转发线程
        threading.Thread(target=self._forward_logs, daemon=True).start()
        
        # 启动监控线程，监控子进程状态
        threading.Thread(target=self._monitor_process, daemon=True).start()
        
        return {"success": True, "message": f"开始执行 {len(selected_courses)} 门课程"}
    
    def _run_task(self, courses: List[Dict], auto_submit: bool, speed: float):
        """执行任务的后台线程"""
        try:
            self._emit_status("task_started", {"total": len(courses)})
            
            # 更新题库提交模式
            if self.tiku and not self.tiku.DISABLE:
                self.tiku.SUBMIT = auto_submit
                self._emit_log("info", f"答题模式: {'自动提交' if auto_submit else '手动保存'}")
            
            # 构建任务配置
            task_config = {
                "speed": speed,
                "jobs": 4,
                "notopen_action": "retry"
            }
            
            total_courses = len(courses)
            stopped_by_user = False
            
            for idx, course in enumerate(courses, 1):
                # 检查停止标志
                if self.should_stop:
                    self._emit_log("warning", "任务已被用户停止")
                    stopped_by_user = True
                    break
                
                course_title = course.get('title', '未知课程')
                self._emit_log("info", f"[{idx}/{total_courses}] 开始学习: {course_title}")
                self._emit_progress({
                    "current": idx,
                    "total": total_courses,
                    "course": course_title,
                    "percent": int((idx - 1) / total_courses * 100)
                })
                
                try:
                    # 包装 process_course 来捕获进度
                    self._process_course_with_logging(course, task_config)
                    
                    # 课程完成后再次检查停止标志
                    if self.should_stop:
                        self._emit_log("warning", "任务已被用户停止")
                        stopped_by_user = True
                        break
                        
                    self._emit_log("success", f"课程 '{course_title}' 学习完成")
                except Exception as e:
                    # 检查是否是用户停止导致的异常
                    if self.should_stop:
                        self._emit_log("warning", "任务已被用户停止")
                        stopped_by_user = True
                        break
                    self._emit_log("error", f"课程 '{course_title}' 学习失败: {e}")
                    traceback.print_exc()
                
                self._emit_progress({
                    "current": idx,
                    "total": total_courses,
                    "course": course_title,
                    "percent": int(idx / total_courses * 100)
                })
            
            if stopped_by_user:
                self._emit_log("info", "任务已停止")
                self._emit_status("task_stopped")
            else:
                self._emit_log("success", "所有任务执行完成!")
                self._emit_status("task_completed")
            
        except Exception as e:
            self._emit_log("error", f"任务执行异常: {e}")
            traceback.print_exc()
            self._emit_status("task_error", {"error": str(e)})
        finally:
            self.task_running = False
            self.should_stop = False
    
    def _process_course_with_logging(self, course: Dict, config: Dict):
        """带日志的课程处理"""
        # 获取章节列表
        self._emit_log("info", f"正在获取章节列表...")
        point_list = self.chaoxing.get_course_point(
            course["courseId"], course["clazzId"], course["cpi"]
        )
        
        total_points = len(point_list.get("points", []))
        self._emit_log("info", f"共 {total_points} 个章节")
        
        # 调用原有的处理函数
        process_course(self.chaoxing, course, config)
    
    def _forward_logs(self):
        """转发子进程日志到前端"""
        while self.task_running:
            try:
                # 从队列获取日志（超时0.5秒）
                log_entry = self.log_queue.get(timeout=0.5)
                if log_entry:
                    level = log_entry.get("level", "info")
                    message = log_entry.get("message", "")
                    self._emit_log(level, message)
            except:
                # 队列为空或超时，继续循环
                pass
    
    def _monitor_process(self):
        """监控子进程状态"""
        if self.current_process:
            self.current_process.join()  # 等待进程结束
            exit_code = self.current_process.exitcode
            
            # 清空剩余日志
            try:
                while not self.log_queue.empty():
                    log_entry = self.log_queue.get_nowait()
                    if log_entry:
                        self._emit_log(log_entry.get("level", "info"), log_entry.get("message", ""))
            except:
                pass
            
            if self.should_stop:
                self._emit_log("info", "任务已被强制停止")
                self._emit_status("task_stopped")
            elif exit_code == 0:
                self._emit_log("success", "所有任务执行完成!")
                self._emit_status("task_completed")
            else:
                self._emit_log("error", f"任务异常退出 (code: {exit_code})")
                self._emit_status("task_error", {"error": f"进程异常退出: {exit_code}"})
            
            self.task_running = False
            self.should_stop = False
            self.current_process = None
    
    def stop_task(self):
        """停止当前任务 - 直接终止进程"""
        if self.task_running and self.current_process:
            self.should_stop = True
            self._emit_log("warning", "正在强制停止任务...")
            self._emit_status("task_stopping")
            
            try:
                # 直接终止进程
                self.current_process.terminate()
                # 等待最多2秒
                self.current_process.join(timeout=2)
                
                # 如果还没结束，强制杀死
                if self.current_process.is_alive():
                    self.current_process.kill()
                    self.current_process.join(timeout=1)
                
                self._emit_log("success", "任务已强制停止")
                return {"success": True, "message": "任务已停止"}
            except Exception as e:
                self._emit_log("error", f"停止任务失败: {e}")
                return {"success": False, "message": str(e)}
        return {"success": False, "message": "没有运行中的任务"}
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            "logged_in": self.is_logged_in,
            "username": self.account.username if self.account else None,
            "task_running": self.task_running,
            "courses_count": len(self.all_courses)
        }


# 全局任务管理器
task_manager = WebTaskManager()


# ============ 路由 ============

@app.route('/auth')
def auth_page():
    """密码验证页面"""
    if session.get('authenticated'):
        return redirect(url_for('index'))
    return render_template('auth.html')


@app.route('/api/auth', methods=['POST'])
def api_auth():
    """密码验证接口"""
    data = request.json
    password = data.get('password', '').strip()
    
    if not password:
        time.sleep(1)  # 防止暴力破解
        return jsonify({"success": False, "message": "请输入访问密码"})
    
    # 验证密码哈希
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    if input_hash == ACCESS_PASSWORD_HASH:
        session['authenticated'] = True
        session.permanent = True
        return jsonify({"success": True, "message": "验证成功"})
    else:
        time.sleep(2)  # 失败延迟，防止暴力破解
        return jsonify({"success": False, "message": "密码错误"})


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """退出验证"""
    session.clear()
    return jsonify({"success": True, "message": "已退出"})


@app.route('/')
@require_auth
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/login', methods=['POST'])
@require_auth
def api_login():
    """登录接口"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"success": False, "message": "请输入账号和密码"})
    
    result = task_manager.login(username, password)
    return jsonify(result)


@app.route('/api/courses', methods=['GET'])
@require_auth
def api_get_courses():
    """获取课程列表"""
    result = task_manager.get_courses()
    return jsonify(result)


@app.route('/api/task/start', methods=['POST'])
@require_auth
def api_start_task():
    """开始任务"""
    data = request.json
    course_ids = data.get('course_ids', [])
    auto_submit = data.get('auto_submit', False)
    speed = data.get('speed', 2.0)
    
    result = task_manager.start_task(course_ids, auto_submit, speed)
    return jsonify(result)


@app.route('/api/task/stop', methods=['POST'])
@require_auth
def api_stop_task():
    """停止任务"""
    result = task_manager.stop_task()
    return jsonify(result)


@app.route('/api/status', methods=['GET'])
@require_auth
def api_status():
    """获取状态"""
    result = task_manager.get_status()
    return jsonify(result)


@app.route('/api/config/ai', methods=['GET'])
@require_auth
def api_get_ai_config():
    """获取 AI 配置"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    
    try:
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf8')
        
        provider = config.get('tiku', 'provider', fallback='AI')
        
        # 根据 provider 返回对应的配置
        if provider == 'SiliconFlow':
            ai_config = {
                "provider": provider,
                "endpoint": config.get('tiku', 'siliconflow_endpoint', fallback='https://api.siliconflow.cn/v1/chat/completions'),
                "key": config.get('tiku', 'siliconflow_key', fallback=''),
                "model": config.get('tiku', 'siliconflow_model', fallback='deepseek-ai/DeepSeek-V3'),
                "min_interval_seconds": config.get('tiku', 'min_interval_seconds', fallback='3'),
                "submit": config.get('tiku', 'submit', fallback='true'),
                "cover_rate": config.get('tiku', 'cover_rate', fallback='0.9'),
            }
        else:
            ai_config = {
                "provider": provider,
                "endpoint": config.get('tiku', 'endpoint', fallback=''),
                "key": config.get('tiku', 'key', fallback=''),
                "model": config.get('tiku', 'model', fallback=''),
                "min_interval_seconds": config.get('tiku', 'min_interval_seconds', fallback='3'),
                "submit": config.get('tiku', 'submit', fallback='true'),
                "cover_rate": config.get('tiku', 'cover_rate', fallback='0.9'),
            }
        
        return jsonify({"success": True, "config": ai_config})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/config/ai/test', methods=['POST'])
@require_auth
def api_test_ai_config():
    """测试 AI API 连接"""
    try:
        data = request.json
        endpoint = data.get('endpoint', '').strip()
        key = data.get('key', '').strip()
        model = data.get('model', '').strip()
        
        if not endpoint or not key or not model:
            return jsonify({"success": False, "message": "请填写完整的 API 配置"})
        
        # 处理 endpoint：如果包含 /chat/completions，去掉它（OpenAI SDK 会自动添加）
        base_url = endpoint.replace('/chat/completions', '').rstrip('/')
        
        # 使用 OpenAI SDK 测试连接
        from openai import OpenAI
        
        client = OpenAI(
            api_key=key,
            base_url=base_url
        )
        
        # 发送一个简单的测试请求
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "请回复：连接成功"}
            ],
            max_tokens=20,
            timeout=15
        )
        
        reply = response.choices[0].message.content
        return jsonify({
            "success": True, 
            "message": f"连接成功！模型回复: {reply[:50]}"
        })
        
    except Exception as e:
        error_msg = str(e)
        if "NotFoundError" in error_msg or "Not Found" in error_msg:
            return jsonify({"success": False, "message": f"API 路径或模型不存在，请检查 Endpoint 和模型名称"})
        elif "AuthenticationError" in error_msg or "401" in error_msg:
            return jsonify({"success": False, "message": "API Key 无效或已过期"})
        elif "timeout" in error_msg.lower():
            return jsonify({"success": False, "message": "连接超时，请检查网络或 Endpoint"})
        else:
            return jsonify({"success": False, "message": f"连接失败: {error_msg}"})


@app.route('/api/config/ai', methods=['POST'])
@require_auth
def api_save_ai_config():
    """保存 AI 配置"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    
    try:
        data = request.json
        
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf8')
        
        # 确保 tiku 节存在
        if not config.has_section('tiku'):
            config.add_section('tiku')
        
        provider = data.get('provider', 'AI')
        config.set('tiku', 'provider', provider)
        
        # 根据 provider 保存到对应的字段
        if provider == 'SiliconFlow':
            # 硅基流动使用专用字段
            if 'endpoint' in data:
                config.set('tiku', 'siliconflow_endpoint', data['endpoint'])
            if 'key' in data:
                config.set('tiku', 'siliconflow_key', data['key'])
            if 'model' in data:
                config.set('tiku', 'siliconflow_model', data['model'])
        else:
            # 通用 AI 配置
            if 'endpoint' in data:
                config.set('tiku', 'endpoint', data['endpoint'])
            if 'key' in data:
                config.set('tiku', 'key', data['key'])
            if 'model' in data:
                config.set('tiku', 'model', data['model'])
        
        # 通用配置
        if 'min_interval_seconds' in data:
            config.set('tiku', 'min_interval_seconds', str(data['min_interval_seconds']))
        if 'submit' in data:
            config.set('tiku', 'submit', str(data['submit']).lower())
        if 'cover_rate' in data:
            config.set('tiku', 'cover_rate', str(data['cover_rate']))
        
        # 确保 true_list 和 false_list 存在（判断题必需）
        if not config.has_option('tiku', 'true_list'):
            config.set('tiku', 'true_list', '正确,对,√,是')
        if not config.has_option('tiku', 'false_list'):
            config.set('tiku', 'false_list', '错误,错,×,否,不对,不正确')
        
        # 保存配置文件
        with open(config_path, 'w', encoding='utf8') as f:
            config.write(f)
        
        # 重新加载配置到任务管理器
        task_manager._load_config()
        
        return jsonify({"success": True, "message": "配置已保存"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# ============ WebSocket 事件 ============

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    pass


# ============ 独立进程任务函数 ============

def run_task_in_process(username: str, password: str, courses: List[Dict], 
                        tiku_config: Dict, auto_submit: bool, speed: float,
                        log_queue: multiprocessing.Queue):
    """在独立进程中执行任务（可被 terminate 直接杀死）"""
    
    def send_log(level: str, message: str):
        """发送日志到队列"""
        try:
            log_queue.put({"level": level, "message": message})
        except:
            pass
    
    try:
        send_log("info", "正在初始化任务...")
        
        # 重新初始化所有对象（进程间不共享内存）
        account = Account(username, password)
        
        # 初始化题库
        tiku = Tiku()
        tiku.config_set(tiku_config)
        tiku = tiku.get_tiku_from_config()
        tiku.init_tiku()
        tiku.SUBMIT = auto_submit
        
        tiku_name = tiku.name if hasattr(tiku, 'name') and tiku.name else '已禁用'
        send_log("info", f"题库: {tiku_name}")
        
        # 获取查询延迟设置
        query_delay = tiku_config.get("delay", 0)
        
        # 初始化超星实例
        chaoxing = Chaoxing(
            account=account,
            tiku=tiku,
            query_delay=query_delay
        )
        
        # 登录
        send_log("info", "正在登录...")
        login_result = chaoxing.login(login_with_cookies=False)
        if not login_result["status"]:
            send_log("error", f"登录失败: {login_result['msg']}")
            sys.exit(1)
        
        send_log("success", "登录成功，开始执行任务...")
        
        # 构建任务配置
        task_config = {
            "speed": speed,
            "jobs": 4,
            "notopen_action": "retry"
        }
        
        # 执行每个课程
        total_courses = len(courses)
        for idx, course in enumerate(courses, 1):
            course_title = course.get('title', '未知课程')
            send_log("info", f"[{idx}/{total_courses}] 开始学习: {course_title}")
            
            try:
                # 获取章节数量
                point_list = chaoxing.get_course_point(
                    course["courseId"], course["clazzId"], course["cpi"]
                )
                total_points = len(point_list.get("points", []))
                send_log("info", f"共 {total_points} 个章节")
                
                process_course(chaoxing, course, task_config)
                send_log("success", f"课程 '{course_title}' 学习完成")
            except Exception as e:
                send_log("error", f"课程 '{course_title}' 学习失败: {e}")
                traceback.print_exc()
        
        send_log("success", "所有任务执行完成!")
        sys.exit(0)
        
    except Exception as e:
        send_log("error", f"任务执行异常: {e}")
        traceback.print_exc()
        sys.exit(1)


# ============ 入口 ============

def open_browser():
    """延迟打开浏览器"""
    import webbrowser
    time.sleep(1)  # 等待服务器启动
    webbrowser.open('http://127.0.0.1:7002')

if __name__ == '__main__':
    print("=" * 50)
    print("  超星学习通 Web 可视化界面")
    print("  访问地址: http://127.0.0.1:7002")
    print("=" * 50)
    
    # 自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    socketio.run(app, host='0.0.0.0', port=7002, debug=False, allow_unsafe_werkzeug=True)
