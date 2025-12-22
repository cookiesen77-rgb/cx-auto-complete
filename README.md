# 超星学习通自动化助手

一款开源的超星学习通自动化工具，支持 Web 可视化界面和 AI 智能答题。

## 功能特性

- **Web 可视化界面** - 现代化 UI，实时日志，一键操作
- **AI 智能答题** - 支持 OpenAI 兼容接口、硅基流动等多种 AI 服务
- **多题库支持** - 言溪题库、LIKE 知识库、TikuAdapter 等
- **自动完成任务点** - 视频观看、章节检测、答题等
- **跨平台支持** - Windows / macOS / Linux

## 快速开始

### Windows 用户

1. 下载或克隆本项目
2. 双击运行 `start.bat`
3. 首次运行会自动创建虚拟环境并安装依赖
4. 浏览器自动打开 http://127.0.0.1:7002

### macOS 用户

1. 下载或克隆本项目
2. 双击运行 `start.command`（首次需要右键 → 打开）
3. 首次运行会自动创建虚拟环境并安装依赖
4. 浏览器自动打开 http://127.0.0.1:7002

### Linux 用户

```bash
chmod +x start.sh
./start.sh
```

## 访问密码

首次访问需要输入密码：`314394`

## 使用方法

1. 启动 Web 界面
2. 输入访问密码进入
3. 输入手机号和密码登录学习通
4. 选择要学习的课程
5. 配置 AI 答题（可选）
6. 点击「开始学习」

## AI 答题配置

点击界面「AI CONFIG」按钮，支持：

| 类型 | 说明 |
|------|------|
| AI (OpenAI 兼容) | 支持 OpenAI、DeepSeek、通义千问等兼容接口 |
| SiliconFlow | 硅基流动 AI 服务（推荐，有免费额度） |
| TikuYanxi | 言溪题库 |
| TikuLike | LIKE 知识库 |
| TikuAdapter | 开源题库适配器 |

### 推荐配置（硅基流动）

1. 访问 https://cloud.siliconflow.cn/ 注册账号
2. 获取 API Key
3. 在 AI 配置中选择 `SiliconFlow`
4. 填入 API Key，模型选择 `deepseek-ai/DeepSeek-V3.2`

## 命令行模式

```bash
# 激活虚拟环境后运行
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
provider = SiliconFlow
siliconflow_key = your-api-key
siliconflow_model = deepseek-ai/DeepSeek-V3.2
submit = true
cover_rate = 0.9
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
├── start.bat           # Windows 启动脚本
├── start.command       # macOS 启动脚本
├── start.sh            # Linux 启动脚本
└── config_template.ini # 配置模板
```

## 依赖安装（手动）

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python web_app.py
```

## 常见问题

### Q: 启动时提示 "未检测到 Python"
A: 请先安装 Python 3.9 或更高版本，访问 https://www.python.org/downloads/

### Q: 依赖安装失败
A: 检查网络连接，或尝试使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: macOS 提示 "无法打开，因为无法验证开发者"
A: 右键点击 `start.command` → 选择「打开」→ 点击「打开」

### Q: Windows 提示 "Windows 保护了你的电脑"
A: 点击「更多信息」→「仍要运行」

## 免责声明

- 本项目仅供学习交流使用
- 禁止用于商业用途
- 使用本工具产生的任何后果由使用者自行承担

## License

GPL-3.0
