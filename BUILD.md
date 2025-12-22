# 应用打包说明

## 打包步骤

### Windows

1. 双击运行 `build_app.bat`
2. 等待打包完成（约 2-5 分钟）
3. 打包完成后，应用位于 `dist/超星学习通/` 目录

### macOS / Linux

```bash
chmod +x build_app.sh
./build_app.sh
```

打包完成后，应用位于 `dist/超星学习通/` 目录

## 运行打包后的应用

### Windows

```bash
cd dist\超星学习通
超星学习通.exe
```

### macOS / Linux

```bash
cd dist/超星学习通
./超星学习通
```

浏览器自动打开 http://127.0.0.1:8080

## 分发应用

将整个 `dist/超星学习通/` 文件夹打包成 zip，分发给其他用户即可。

用户解压后直接运行可执行文件，无需安装 Python 环境。

## 注意事项

- 首次运行需要配置 AI 答题（点击界面左下角「AI 答题配置」）
- 可以复制 `config.ini` 到应用目录进行预配置
- 打包后的应用体积约 200-300MB（包含所有依赖）
- macOS 用户首次运行可能需要在「系统偏好设置 > 安全性与隐私」中允许运行

## 打包文件说明

- `cx_app.spec` - PyInstaller 配置文件
- `build_app.bat` - Windows 打包脚本
- `build_app.sh` - macOS/Linux 打包脚本
