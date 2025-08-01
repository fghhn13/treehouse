# ai_service/tongyi_client.py
import os
import dashscope
from dashscope import Generation
import json
import asyncio
from dotenv import load_dotenv

# --- 加载配置 ---
load_dotenv()

def load_prompt_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'prompt_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"错误：读取 prompt_config.json 失败: {e}")
        return None

def build_system_prompt(config):
    if not config:
        return "Please respond in JSON." # Fallback

    examples_str_list = []
    for example in config.get("examples", []):
        user_input = example.get("user_input")
        ai_output = json.dumps(example.get("ai_output"), ensure_ascii=False, indent=2)
        examples_str_list.append(f"例如，如果用户说“{user_input}”，你应该回复类似这样的JSON：\n{ai_output}")

    examples_section = "\n\n".join(examples_str_list)
    # --- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ---

    prompt_parts = [
        config.get("base_persona"),
        config.get("json_format_instruction"),
        config.get("expression_list_instruction"),
        ", ".join(config.get("available_expressions", [])),
        examples_section,  # <-- 使用我们新构建的范例字符串
        config.get("final_instruction")
    ]
    return "\n\n".join(filter(None, prompt_parts))


prompt_config = load_prompt_config()
SYSTEM_PROMPT = build_system_prompt(prompt_config)


# --- 核心API调用函数 ---
def call_tongyi_sync(user_message: str):
    """
    这是一个同步函数，因为它将在一个独立的线程中运行。
    """
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key:
        print("错误：DASHSCOPE_API_KEY 环境变量未设置！")
        return {"reply_text": "我的大脑连接好像出了一点问题...", "expression": "upset"}

    try:
        print(f"正在向通义千问发送消息: '{user_message}'")
        response = Generation.call(
            model='qwen-turbo',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_message}
            ],
            result_format='text'
        )

        if response.status_code == 200:
            response_text = response.output.text.strip()
            print(f"收到通义千问原始回复: {response_text}")

            ai_script = json.loads(response_text)

            # vvvvvvvvvv 在这里更新我们的检查逻辑 vvvvvvvvvvvv
            # 把检查 "motion" 改成检查 "expression"
            if "reply_text" in ai_script and "expression" in ai_script:
                # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                return ai_script
            else:
                print("错误：通义千问返回的JSON格式不正确。")
                return {"reply_text": "我好像有点短路了...", "expression": "upset"}
        else:
            print(f"通义千问API返回错误: Status Code {response.status_code}, Message: {response.message}")
            return {"reply_text": "呜哇，和大脑的连接好像中断了...", "expression": "sad"}

    except Exception as e:
        print(f"调用通义千问API时发生严重错误: {e}")
        return {"reply_text": "我的大脑过载啦！稍等一下！", "expression": "surprise"}
async def get_tongyi_response(user_message: str):
    """
    异步包装器，让同步的SDK调用不阻塞FastAPI主线程。
    """
    loop = asyncio.get_running_loop()
    # 在一个单独的线程中运行同步的API调用
    ai_script = await loop.run_in_executor(
        None, call_tongyi_sync, user_message
    )
    return ai_script