# main.py (终极整合版 by Nana酱)

import asyncio
import json
import random
import datetime  # [新] 导入datetime模块
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from typing import List

# [新] 导入我们新建的数据库模块和AI服务
from database import SessionLocal, AIStatus, init_db
from ai_service.tongyi_client import get_tongyi_response

# [新] 导入APScheduler，我们的新版生活节律器
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# --- 1. 配置信息 ---
# 确保前端项目是打包到这个 "static" 文件夹里的
STATIC_FILES_DIR = "static"

# 智能体生命周期配置
AGENT_STATUS = "home"  # 初始状态
HOME_MIN_SECONDS = 1500
HOME_MAX_SECONDS = 3000
AWAY_MIN_SECONDS = 10
AWAY_MAX_SECONDS = 20
HAPPY_EXPRESSIONS = ["happy", "smile", "proud", "starry_eyes"]

# --- 2. WebSocket 管理器 ---
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

# --- 3. 智能体生命周期模拟 ---
async def switch_to_home():
    global AGENT_STATUS
    AGENT_STATUS = "home"
    print(f"【状态切换】: 智能体已回家！")
    status_update_msg = {"type": "status_update", "status": "home"}
    await manager.broadcast(json.dumps(status_update_msg))

async def switch_to_away():
    global AGENT_STATUS
    AGENT_STATUS = "away"
    print(f"【状态切换】: 智能体已出发旅行。")
    status_update_msg = {"type": "status_update", "status": "away"}
    await manager.broadcast(json.dumps(status_update_msg))

async def agent_life_cycle():
    print("智能体生命周期服务已启动...")
    while True:
        if AGENT_STATUS == "away":
            sleep_time = random.uniform(AWAY_MIN_SECONDS, AWAY_MAX_SECONDS)
            print(f"智能体正在旅行，预计 {sleep_time:.1f} 秒后回家...")
            await asyncio.sleep(sleep_time)
            await switch_to_home()
        elif AGENT_STATUS == "home":
            sleep_time = random.uniform(HOME_MIN_SECONDS, HOME_MAX_SECONDS)
            print(f"智能体正在家，{sleep_time:.1f} 秒后将出发旅行...")
            await asyncio.sleep(sleep_time)
            await switch_to_away()

# --- 4. FastAPI 应用主体 ---
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """在服务启动时，自动开启智能体的生命周期循环。"""
    asyncio.create_task(agent_life_cycle())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """处理WebSocket连接和真实的用户输入。"""
    await manager.connect(websocket)
    print(f"新用户连接，当前状态: {AGENT_STATUS}")
    initial_status = {"type": "status_update", "status": AGENT_STATUS}
    await websocket.send_text(json.dumps(initial_status))

    try:
        while True:
            user_message = await websocket.receive_text()
            if AGENT_STATUS == "home":
                ai_script = await get_tongyi_response(user_message)

                # vvvvvv 在这里添加我们的编舞逻辑 vvvvvv
                expression = ai_script.get("expression")
                if expression in HAPPY_EXPRESSIONS:
                    ai_script["motion"] = "TapBody"  # 开心表情 -> TapBody动作组
                else:
                    ai_script["motion"] = "Idle"  # 其他表情 -> Idle动作组
                # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

                response_command = {"type": "ai_response", "data": ai_script}
                await manager.broadcast(json.dumps(response_command))
            else:
                # 如果不在家，就只给当前这个发送消息的用户一个回复
                response_command = {
                    "type": "ai_response",
                    "data": {"reply_text": "我现在不在家，稍后回来再聊哦~", "motion": "Idle"}
                }
                await websocket.send_text(json.dumps(response_command))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("一个用户已断开连接")

# --- 5. 保留的调试API接口 ---
@app.get("/api/say")
async def say_something(message: str):
    # ... (函数上半部分不变) ...
    if AGENT_STATUS == "home":
        ai_script = await get_tongyi_response(message)

        # vvvvvv 同样在这里添加我们的编舞逻辑 vvvvvv
        expression = ai_script.get("expression")
        if expression in HAPPY_EXPRESSIONS:
            ai_script["motion"] = "TapBody"
        else:
            ai_script["motion"] = "Idle"
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        response_command = {"type": "ai_response", "data": ai_script}
        await manager.broadcast(json.dumps(response_command))
        return {"status": "ok", "message_sent": message, "ai_response": ai_script}
    else:
        return {"status": "ignored", "reason": "Agent is away."}

@app.get("/api/do_motion")
async def do_motion():
    """【保留功能】快速测试播放一个固定的动作。"""
    print("【调试指令】收到do_motion请求")
    command = {"type": "motion", "group": "TapBody"}
    await manager.broadcast(json.dumps(command))
    return {"status": "ok", "command_sent": command}

# --- 6. 挂载静态文件 ---
# 确保这行在文件最末尾，为前端提供服务
app.mount("/", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="static")