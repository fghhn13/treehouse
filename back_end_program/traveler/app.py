# app.py (究极合体版 by Nana酱)

# --- 1. 导入所有需要的“法术书” ---
import sys
import os
import argparse
import uvicorn
import asyncio
import json
import random
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from typing import List
from contextlib import asynccontextmanager

# 导入 APScheduler，我们的新版生活节律器
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# 导入我们新建的数据库模块和AI服务
# (请确保这些文件和文件夹在你的项目里是存在的哦！)
# from database import SessionLocal, AIStatus, init_db
from ai_service.qwen.tongyi_client import get_tongyi_response

# --- 2. 修正模块搜索路径 ---
# 将项目根目录 (treehouse) 添加到Python的模块搜索路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- 3. 全局配置 ---
AGENT_STATUS = "home"  # 初始状态
HAPPY_EXPRESSIONS = ["happy", "smile", "proud", "starry_eyes"]


# --- 4. WebSocket 管理器 (无变化) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()
scheduler = AsyncIOScheduler()  # [新] 创建调度器实例


# --- 5. 智能体生命周期 (APScheduler 精准控制版) ---
async def switch_to_status(status: str):
    """[新] 统一的状态切换函数"""
    global AGENT_STATUS

    if status == AGENT_STATUS:
        return  # 如果状态没变，就不做任何事

    AGENT_STATUS = status
    print(f"【状态切换】: 智能体状态变为 -> {status.upper()}!")

    status_update_msg = {"type": "status_update", "status": status}
    await manager.broadcast(json.dumps(status_update_msg))

    # 移除旧的计划任务，安排新的
    if scheduler.get_job('life_cycle_switch'):
        scheduler.remove_job('life_cycle_switch')

    if status == "home":
        # 如果现在是回家状态，就计划一个随机时间后出门
        delay = random.uniform(15, 30)  # 为了方便测试，暂时缩短在家时间
        scheduler.add_job(switch_to_status, 'date',
                          run_date=datetime.datetime.now() + datetime.timedelta(seconds=delay), args=['away'],
                          id='life_cycle_switch')
        print(f"智能体正在家，计划在 {delay:.1f} 秒后出发旅行...")
    elif status == "away":
        # 如果现在是出门状态，就计划一个随机时间后回家
        delay = random.uniform(10, 20)
        scheduler.add_job(switch_to_status, 'date',
                          run_date=datetime.datetime.now() + datetime.timedelta(seconds=delay), args=['home'],
                          id='life_cycle_switch')
        print(f"智能体正在旅行，预计 {delay:.1f} 秒后回家...")


# --- 6. FastAPI 应用主体 (使用新的 lifespan 事件) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """ [新] FastAPI 的新版生命周期事件管理器 """
    print("--- 服务器启动流程开始 ---")
    # 在应用启动时执行:

    # 1. 启动调度器
    scheduler.start()
    print("[Lifespan] 智能体生物钟 (APScheduler) 已启动。")

    # 2. 安排第一次状态切换 (例如5秒后出门)
    initial_delay = 5
    scheduler.add_job(switch_to_status, 'date',
                      run_date=datetime.datetime.now() + datetime.timedelta(seconds=initial_delay), args=['away'],
                      id='life_cycle_switch')
    print(f"[Lifespan] 已安排初始任务：{initial_delay}秒后出发去旅行。")

    yield

    # 在应用关闭时执行:
    print("--- 服务器关闭流程开始 ---")
    scheduler.shutdown()
    print("[Lifespan] 智能体生物钟 (APScheduler) 已关闭。")


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f"新用户连接，当前状态: {AGENT_STATUS}")
    initial_status = {"type": "status_update", "status": AGENT_STATUS}
    await websocket.send_text(json.dumps(initial_status))

    try:
        while True:
            user_message = await websocket.receive_text()
            if AGENT_STATUS == "home":
                ai_script = await get_tongyi_response(user_message)
                expression = ai_script.get("expression")
                if expression in HAPPY_EXPRESSIONS:
                    ai_script["motion"] = "TapBody"
                else:
                    ai_script["motion"] = "Idle"
                response_command = {"type": "ai_response", "data": ai_script}
                await manager.broadcast(json.dumps(response_command))
            else:
                response_command = {
                    "type": "ai_response",
                    "data": {"reply_text": "我现在不在家，稍后回来再聊哦~", "motion": "Idle"}
                }
                await websocket.send_text(json.dumps(response_command))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("一个用户已断开连接")


# --- 7. 主函数与程序入口 ---
def start_server(web_path: str, reload: bool):
    # 挂载静态文件必须在 uvicorn.run 之前
    app.mount("/", StaticFiles(directory=web_path, html=True), name="static")
    print(f"静态文件服务已挂载，目录: {web_path}")

    uvicorn.run(
        "__main__:app",  # [重要] 告诉Uvicorn app实例在当前文件里
        host="0.0.0.0",
        port=8000,
        reload=reload
    )


if __name__ == "__main__":
    # 1. 初始化数据库 (如果您的database.py里有这个函数)
    # init_db()
    # print("[Main] 数据库初始化完成。")

    # 2. 解析命令行参数
    parser = argparse.ArgumentParser(description="数字生命后端程序.")
    parser.add_argument("--web-path", default="static", help="Path to the web static files.")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development.")
    args = parser.parse_args()

    # 3. 启动服务器
    print(f"准备启动服务器...")
    print(f"  -> 前端路径: {args.web_path}")
    print(f"  -> 热重载模式: {'开启' if args.reload else '关闭'}")

    start_server(web_path=args.web_path, reload=args.reload)