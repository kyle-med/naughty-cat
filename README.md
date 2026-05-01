# Naughty Cat 🐱

一只会用猫咪提醒你休息的 Windows 桌面小工具。工作时间到了，猫咪们会弹出来在你屏幕上散步、喵喵叫，直到你真的起身休息为止。

## 功能

- **定时提醒** — 可配置工作间隔（3–120分钟），到点自动弹出猫咪
- **猫咪漫步** — 猫咪窗口在桌面上随机方向移动，碰到屏幕边缘会弹跳
- **休息检测** — 通过 Win32 API 检测键盘鼠标空闲，确认你真的离开工位
- **驱赶模式** — 暂时不想休息？点击驱赶，猫咪躲一会儿再来
- **休息完成** — 休息够时间后弹出通知"猫咪出去玩了！"
- **多只猫咪** — 可同时显示1–10只猫咪，每只随机速度和方向
- **自定义猫咪** — 导入自己的 GIF/APNG 猫咪，内置 4 只猫咪（波仔、咣当、Bender、胖虎）
- **音效** — 猫咪出现时播放喵叫，支持自定义音效
- **系统托盘** — 最小化到托盘，右键菜单快速操作
- **开机自启** — 支持注册开机启动项
- **暂停/恢复** — 临时不想被打扰时可以暂停提醒

## 技术栈

| 模块 | 技术 |
|------|------|
| UI 框架 | PySide6 (Qt for Python) |
| 猫咪动画 | QMovie + GIF |
| 空闲检测 | Win32 `GetLastInputInfo` API |
| 音频播放 | QMediaPlayer |
| 配置存储 | JSON + 原子写入 |
| 打包 | PyInstaller |
| 安装程序 | NSIS |
| 测试 | pytest + pytest-qt |

## 架构

```
naughty_cat/
├── main.py                  # 入口，组装各模块
├── state_machine.py         # 6 状态状态机
├── cat_manager.py           # 猫咪窗口生命周期 & 随机漫步
├── idle_detector.py         # 键盘鼠标空闲检测
├── config_store.py          # JSON 配置读写
├── sound_player.py          # 音频播放
├── tray_icon.py             # 系统托盘图标 & 菜单
├── ui/
│   ├── welcome_wizard.py    # 首次运行向导（3步）
│   ├── settings_window.py   # 设置对话框（4标签）
│   ├── cat_config.py        # 猫咪选择面板
│   └── break_done_toast.py  # 休息完成通知
└── assets/
    ├── cats/                # 内置猫咪 GIF
    ├── sounds/              # 内置音效
    └── icons/               # 托盘图标
```

### 状态机

```
WORKING ──工作计时器到──▶ CAT_SHOW
                            ├── 检测到空闲 ──▶ RESTING
                            │                    ├── 用户活动 ──▶ RESTING_PAUSED
                            │                    │                 └── 再次空闲 ──▶ RESTING
                            │                    └── 休息完成 ──▶ REST_DONE
                            │                                       └── 点"知道了"──▶ WORKING
                            └── 点驱赶 ──▶ CAT_HIDING ──▶ CAT_SHOW
```


