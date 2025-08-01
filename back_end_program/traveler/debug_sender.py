# debug_sender.py
import tkinter as tk
from tkinter import scrolledtext
import requests
import threading
import json

# --- 配置 ---
# 你的FastAPI后端地址
API_URL = " http://0.0.0.0:8000/api/say"


# --- 核心功能 ---
def send_message_thread(message):
    """在一个独立的线程中发送消息，防止GUI卡顿"""
    if not message.strip():
        log_to_window("不能发送空消息哦！")
        return

    log_to_window(f"正在发送: {message}")

    try:
        # 发送GET请求，附带URL参数
        response = requests.get(API_URL, params={'message': message}, timeout=30)  # 15秒超时
        response.raise_for_status()  # 如果请求失败 (例如 404, 500), 会抛出异常

        # 在日志窗口显示后端返回的确认信息
        response_data = response.json()
        pretty_response = json.dumps(response_data, indent=2, ensure_ascii=False)
        log_to_window(f"后端回复:\n{pretty_response}")

    except requests.exceptions.RequestException as e:
        log_to_window(f"发送失败！错误: {e}\n(请确认你的FastAPI服务 uvicorn main:app 已经启动)")
    except Exception as e:
        log_to_window(f"发生未知错误: {e}")


def on_send_button_click():
    """处理发送按钮点击事件"""
    message = input_entry.get()
    # 使用线程来发送消息
    threading.Thread(target=send_message_thread, args=(message,)).start()


def log_to_window(text):
    """安全地向日志窗口添加文本 (线程安全)"""
    log_area.config(state=tk.NORMAL)
    log_area.insert(tk.END, text + "\n\n")
    log_area.config(state=tk.DISABLED)
    log_area.see(tk.END)  # 自动滚动到底部


# --- 创建GUI界面 ---
# 主窗口
root = tk.Tk()
root.title("Nana酱的AI指令发送器")
root.geometry("500x400")  # 设置窗口大小

# 标签
main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# 输入框
input_label = tk.Label(main_frame, text="在这里输入想对她说的话:")
input_label.pack(anchor='w')

input_entry = tk.Entry(main_frame, width=50, font=("Arial", 12))
input_entry.pack(fill=tk.X, pady=5)
input_entry.focus()  # 启动时自动聚焦到输入框

# 绑定回车键
input_entry.bind("<Return>", lambda event: on_send_button_click())

# 发送按钮
send_button = tk.Button(main_frame, text="发送指令", command=on_send_button_click, font=("Arial", 12))
send_button.pack(pady=5)

# 日志显示区域
log_label = tk.Label(main_frame, text="日志:")
log_label.pack(anchor='w', pady=(10, 0))

log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state=tk.DISABLED, height=10, font=("Courier New", 10))
log_area.pack(fill=tk.BOTH, expand=True)

# 启动GUI事件循环
root.mainloop()