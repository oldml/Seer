# 赛尔号台服脱机小助手 (Seer TW Offline Helper)

> [!WARNING]
> **重要通知：此仓库已不再维护。**
>
> 所有最新的代码、问题跟踪 (Issues) 和更新都已迁移至新的 GitHub 仓库。请访问以下链接：
>
> ## 👉 [https://github.com/oldml/SeerTaiwanRoutineHelper](https://github.com/oldml/SeerTaiwanRoutineHelper)

> [!NOTE]
> 旧版代码中的注释部分是由 AI 辅助生成的，可能存在不准确之处。请以实际代码逻辑为准。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

本项目是一个基于 Python 开发的赛尔号（台服）脱机辅助工具，旨在自动化处理游戏内的重复性操作，为玩家“护肝”。

## ✨ 功能 (Features)

*   **用户认证系统**：处理用户登录及相关认证逻辑。
*   **宠物战斗管理**：管理宠物战斗的核心逻辑，包括战斗流程和数据包处理。
*   **网络通信模块**：负责处理网络数据包的发送、接收与解析。
*   **核心算法实现**：包含项目所依赖的特定计算逻辑。
*   **UI 配置管理**：通过 `ui_config.py` 管理用户界面的相关参数。

## 🔧 技术栈 (Tech Stack)

*   **主要语言**: Python 3.x
*   **标准库**: `socket`, `threading`， `logging` 等
*   **配置文件**: INI (`config.ini`), JSON (`Command.json`)

## 🚀 快速开始 (Getting Started)

### 1. 环境准备

确保您的环境中已安装 Python 3。

### 2. 克隆与安装

```bash
# 克隆仓库
git clone https://github.com/oldml/Seer.git

# 进入项目目录
cd your-repo-name

# 安装依赖
pip install package_name

# 运行主程序
python ui_config.py
