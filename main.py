# main.py (平台总启动器)
import os
import subprocess
import sys

# 存放 .bat 脚本的文件夹
LAUNCHER_DIR = "launchers"


def find_launchers():
    """查找所有可用的 .bat 启动脚本"""
    if not os.path.exists(LAUNCHER_DIR):
        return []

    launchers = [f for f in os.listdir(LAUNCHER_DIR) if f.endswith(".bat")]
    return launchers


def main_menu():
    """显示主菜单并处理用户选择"""
    print("=" * 40)
    print("      欢迎来到数字生命孵化平台 V1.0")
    print("=" * 40)

    launchers = find_launchers()

    if not launchers:
        print("错误：在 'launchers' 文件夹中没有找到任何启动脚本 (.bat)！")
        sys.exit(1)

    print("请选择一个要启动的“体验预案”:\n")
    for i, launcher_name in enumerate(launchers):
        # 清理一下名字，让它更好看
        pretty_name = launcher_name.replace(".bat", "").replace("start_", " ").replace("_", " ").title()
        print(f"  [{i + 1}] {pretty_name}")

    print(f"  [0] 退出平台")
    print("-" * 40)

    while True:
        try:
            choice = int(input("请输入您的选择 [0-{}]: ".format(len(launchers))))
            if 0 <= choice <= len(launchers):
                break
            else:
                print("无效输入，请输入列表中的数字。")
        except ValueError:
            print("无效输入，请输入数字。")

    if choice == 0:
        print("感谢使用，平台已关闭。")
        sys.exit(0)

    selected_launcher = launchers[choice - 1]
    launcher_path = os.path.join(LAUNCHER_DIR, selected_launcher)

    print(f"\n正在执行预案: {launcher_path} ...")

    try:
        # 使用 Popen 可以在后台启动 .bat 文件，并且我们的主程序可以继续运行或退出
        subprocess.Popen(f'cmd /c start "{selected_launcher}" "{launcher_path}"', shell=True)
        print("启动指令已发送！新的窗口将会打开。")
    except Exception as e:
        print(f"启动失败！错误: {e}")


if __name__ == "__main__":
    main_menu()