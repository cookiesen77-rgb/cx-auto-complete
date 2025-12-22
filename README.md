# 超星学习通自动化助手

一款开源的超星学习通自动化工具，支持 Web 可视化界面和 AI 智能答题。

## 功能特性

- **Web 可视化界面** - 现代化 UI，实时日志，一键操作
- **AI 智能答题** - 支持 OpenAI 兼容接口、硅基流动等多种 AI 服务
- **多题库支持** - 言溪题库、LIKE 知识库、TikuAdapter 等
- **自动完成任务点** - 视频观看、章节检测、答题等
- **跨平台支持** - Windows / macOS / Linux

## 快速开始

### 方式一：独立应用（推荐）

**无需安装 Python 环境，开箱即用**

1. 从 [Releases](https://github.com/cookiesen77-rgb/cx-auto-complete/releases) 下载对应平台的应用包
2. 解压后运行可执行文件
3. 浏览器自动打开 http://127.0.0.1:8080

### 方式二：源码运行

**Windows**

双击运行 `web_start.bat`，浏览器自动打开 http://127.0.0.1:8080

**macOS / Linux**

```bash
chmod +x web_start.sh
./web_start.sh
```

浏览器访问 http://127.0.0.1:8080

## 使用方法

1. 启动 Web 界面
2. 输入手机号和密码登录
3. 选择要学习的课程
4. 配置 AI 答题（可选）
5. 点击「开始学习」

## AI 答题配置

点击界面左下角「AI 答题配置」按钮，支持：

| 类型 | 说明 |
|------|------|
| AI (OpenAI 兼容) | 支持 OpenAI、DeepSeek、通义千问等兼容接口 |
| SiliconFlow | 硅基流动 AI 服务 |
| TikuYanxi | 言溪题库 |
| TikuLike | LIKE 知识库 |
| TikuAdapter | 开源题库适配器 |

## 命令行模式

```bash
# 直接运行
python main.py

# 配置文件运行
python main.py -c config.ini

# 命令行参数
python main.py -u 手机号 -p 密码 -l 课程ID1,课程ID2
```

## 配置文件

复制 `config_template.ini` 为 `config.ini`，按需修改：

```ini
[common]
username = 手机号
password = 密码
speed = 2
jobs = 4

[tiku]
provider = AI
endpoint = https://api.openai.com/v1
key = sk-xxx
model = gpt-4o-mini
submit = true
```

## 项目结构

```
├── web_app.py          # Web 界面主程序
├── main.py             # 命令行主程序
├── api/                # 核心 API 模块
│   ├── base.py         # 超星接口封装
│   ├── answer.py       # 题库和答题
│   └── decode.py       # 页面解析
├── templates/          # Web 模板
├── static/             # 前端资源
└── config_template.ini # 配置模板
```

## 依赖安装

```bash
pip install -r requirements.txt
```

## 打包应用

将项目打包成独立可执行文件：

**Windows**
```bash
build_app.bat
```

**macOS / Linux**
```bash
chmod +x build_app.sh
./build_app.sh
```

打包完成后，应用位于 `dist/超星学习通/` 目录，可直接分发给其他用户使用。

详细说明请查看 [BUILD.md](BUILD.md)

## 免责声明

- 本项目仅供学习交流使用
- 禁止用于商业用途
- 使用本工具产生的任何后果由使用者自行承担

## License

GPL-3.0
