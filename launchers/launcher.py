# launcher.py (V3.0 - 最终版 by Nana酱)

import subprocess
import time
import webbrowser
import platform
import shlex

# --- 可配置区域 ---
# 这是你 app.py 对应的模块路径，完全正确！
BACKEND_MODULE = "back_end_program.traveler.app"
# 前端文件的相对路径
WEB_PATH = "web/static"
# 开启热重载，享受丝滑开发体验！
RELOAD_ENABLED = True
# 浏览器打开的地址
BROWSER_URL = "http://localhost:8000"


def main():
    """主启动函数"""
    print("=" * 50)
    print("      “数字生命”启动器 V3.0 - 最终版")
    print("=" * 50)
    print("\n[1/3] 正在准备启动后端服务...")

    command = [
        "python", "-m", BACKEND_MODULE,
        "--web-path", WEB_PATH
    ]
    if RELOAD_ENABLED:
        command.append("--reload")
        print("      - 热重载模式: 已开启")

    print(f"      - 执行命令: {' '.join(command)}")

    try:
        if platform.system() == "Windows":
            # subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("\n[调试模式] 正在当前窗口直接运行后端，请留意下方的输出...")
            subprocess.run(command)  # 使用 .run() 会等待程序结束，并把日志直接打印在这里
        else:
            terminal_command = f'tell app "Terminal" to do script "{shlex.join(command)}"'
            subprocess.Popen(['osascript', '-e', terminal_command])

        print("\n[2/3] 后端启动指令已发送！请查看弹出的新窗口。")
        print("      正在等待服务启动...")
        time.sleep(5)

        print(f"\n[3/3] 正在打开浏览器，访问 {BROWSER_URL} ...")
        webbrowser.open(BROWSER_URL)

        print("\n" + "=" * 50)
        print("      所有操作已完成！祝您和您的数字生命玩得愉快！")
        print("=" * 50)

    except FileNotFoundError:
        print("\n[错误] 找不到 'python' 命令或模块。")
        print("      请确认您已经正确激活了 Conda 环境。")
    except Exception as e:
        print(f"\n[发生未知错误] {e}")


if __name__ == "__main__":
    main()