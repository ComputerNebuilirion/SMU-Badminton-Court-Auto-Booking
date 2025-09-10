# SMU 羽毛球自动预约助手

一套「零配置」图形界面 + 后台定时抢场的小工具，专为南方医科大学羽毛球场地预约设计，也适用于任何同类型「提前 2 天 0 点放号」场景。

Made by CompNebula

---

## ✨ 主要功能

| 功能 | 说明 |
| ---- | ---- |
| **即时预约** | 今天/明天/后天任意时段，一键抢场 |
| **定时抢场** | 选择「大后天」→ 后台等到 **23:59:00** 自动登录，并等到**0点**开抢，主界面可关闭 |
| **取消定时** | 随时终止后台计时，重新选择日期 |
| **跨机运行** | 打包后仅需官方 Chrome，无需 Python / 驱动 |

---

## 🚀 快速开始（Windows 为例）

1. 安装官方 Chrome（任意稳定版）  
2. 解压 release 压缩包 → 得到两个文件：
SMUBooker.exe          # 主程序
booking_daemon.exe     # 后台计时器
复制
3. 双击 `SMUBooker.exe`  
- 填账号/密码/姓名 → 选场地、时段  
- 若选「大后天」→ 点「确定」→ 提示「计时已在后台运行」→ 主界面可关闭  
4. 到点自动抢场，成功后弹窗提示；失败写日志

---

## 🛠️ 自己打包（可选）

```bash
# 1. 克隆源码
git clone https://github.com/your_name/SMU-Badminton-AutoBook.git
cd SMU-Badminton-AutoBook

# 2. 安装依赖
pip install -r requirements.txt          # wxPython / selenium / schedule / pyinstaller

# 3. 一键打包（生成无窗口 exe）
pyinstaller SMUBooker.spec           # 主程序
pyinstaller booking_daemon.spec         # 后台守护
```

输出在 dist/ 文件夹，直接运行即可。**需保证SMUBooker.exe与booking_daemon.exe在同一目录下**
## 📂 文件说明

| 文件 | 说明 |
| ---- | ---- |
| main.py | 	图形界面 + 取消定时逻辑| 
| booking_daemon.py | 	后台计时，到点唤醒主程序抢场| 
| SMUBadmintonAutoBook.py | 	核心业务函数（登录/选场/提交）| 
| main.spec / daemon.spec | 	PyInstaller 打包配置（已含无窗口、路径等）| 

## ⚠️ 注意事项

首次运行需联网，让 Selenium Manager 自动下载对应 chromedriver；后续断网也能用

定时抢场前请保持电脑不休眠（或设置 Wake-On-LAN / 计划任务）

若 Chrome 自动升级大版本，再次联网即可自动更新驱动

若出现报错提示"Unable to obtain driver for chrome",请运行chrometest.exe下载驱动,等待程序出现"按回车键退出"字样后即可运行抢场程序。

📄 License
MIT © 2025 CompNebula
Fork & Star 欢迎贡献！

