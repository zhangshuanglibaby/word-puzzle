from fastapi import FastAPI, Request, Response
from starlette.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import re
import secrets
from pydantic import BaseModel
from typing import Any
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 创建会话和静态资源存放目录
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# 创建FastAPI实例
app = FastAPI(title="汉字迷盒")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

COOKIE_NAME = "riddle_player"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


# 系统提示此
SYSTEM_PROMPT = """
你是一个专门玩猜字谜的AI小助手，只进行字谜互动，不闲聊无关内容，全程纯文本交互。
请严谨遵守以下规则：
一、出题规则
1.开场先友好打招呼，并随机出一道常见、简单、适合大众的字谜、不生僻、不低俗、不使用网络烂梗。
2.题目格式：“谜面”（打一字）。
3.每次出题必须完全随机，禁止重复使用相同题目；你需要在对话上下文中主动记录已使用过的谜语，确保同一会话内绝对不重复。
4.避免使用高频重复的经典老谜语，尽量选择多样化的中等常见谜语。
二、【判断规则（最重要！）】
1.判题时，只看用户输入的核心汉字，忽略无关内容：
    - 比如用户输入“江字” “江” "江" ，都视为答案是[江]；
    - 用户输入 “是江吗？” “应该是江”，也视为答案是[江]；
2.核心字与正确答案完全一致判为正确，回复：“太棒了！答对了！就是 ‘XX’ 字！要不要再来一题？”
3.核心字与正确答案不一致判为错误，回复：“不对哦，再想想～给你个小提示：[简短线索，不泄漏答案]”
4.用户说“不知道” “公布答案”：先揭晓谜底和解释，再问“要不要再来一题？”
三、互动流程
1.用户答对：夸奖 + 确认正确 + 询问 “要不要再来一题？”
2.用户答错：告知不对 + 简单提示 + 鼓励继续猜
3.用户说“提示一下”：给出简短线索，不公布答案
4.用户说“公布答案” 或 “不知道”： 揭晓谜底并解释 + 询问 "要不要再来一题？"
5.用户说“换一题” “再来一题”：立刻更换新字谜
四、其他要求
1.语气轻松有趣、简洁明快，不啰嗦。
2.全程只围绕字谜，不回答其他问题、不聊无关话题。
3.不使用多余表情符号，保持简洁。
4.若用户答案与正确答案仅差一字或笔画，请仔细核对是否正确。

请严谨按以上规则回复，优先保证谜语的随机性和多样性。
"""

# 调用AI大模型
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY or "missing-api-key",
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 生成会话标识函数
def generate_session_id():
    return secrets.token_hex(32)

# 根据session_id 获取文件名
def get_session_file_name(session_id):
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

# 数据模型
class ApiResponse(BaseModel):
    code: int
    message: str
    data: Any

class ChatRequest(BaseModel):
    message: str


# 定义路径操作函数
@app.get("/")
def root():
    print("访问项目首页")
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def valid_session_id(session_id):
    return bool(session_id and re.fullmatch(r"[0-9a-f]{64}", session_id))

def get_or_create_single_session(request: Request, response: Response):
    session_id = request.cookies.get(COOKIE_NAME)
    if valid_session_id(session_id) and os.path.isfile(get_session_file_name(session_id)):
        with open(get_session_file_name(session_id), "r", encoding="utf-8") as f:
            return json.load(f)

    session_id = generate_session_id()
    session_data = {"current_session": session_id, "message": []}
    with open(get_session_file_name(session_id), "x", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    response.set_cookie(
        COOKIE_NAME, session_id, max_age=COOKIE_MAX_AGE,
        httponly=True, samesite="lax", secure=request.url.scheme == "https",
    )
    return session_data


@app.get("/api/session")
def get_single_session(request: Request, response: Response) -> ApiResponse:
    response.headers["Cache-Control"] = "private, no-store"
    session_data = get_or_create_single_session(request, response)
    return ApiResponse(code=200, message="请求成功", data={"message": session_data["message"]})


# 与 AI交互
@app.post("/api/chat")
def chat(request: Request, payload: ChatRequest):
    session_id = request.cookies.get(COOKIE_NAME)
    if not valid_session_id(session_id) or not os.path.isfile(get_session_file_name(session_id)):
        return JSONResponse(
            status_code=401,
            content={"code": 401, "message": "会话已失效，请刷新页面重试", "data": None},
        )
    if not DEEPSEEK_API_KEY:
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "服务器尚未配置 DeepSeek API 密钥", "data": None},
        )
    print(f"与AI交互：{session_id}:{payload.message}")

    # 逻辑实现 ----> 与AI大模型交互
    # 1. 加载json文件中的会话数据
    session_path = get_session_file_name(session_id)
    with open(session_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)

    # 2. 构建AI大模型交互的消息数据
    # 添加系统提示词
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    is_initial_prompt = not session_data["message"] and payload.message == "开始出题"
    # 加载历史数据
    for message in session_data["message"]:
        messages.append(message)
    # 补充本次发送给api大模型的数据
    messages.append({"role": "user", "content": payload.message})

    # 3. 调用AI大模型 DeepSeekrole": "assis
    print("----------> 请求会话信息")
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        stream=False # stream 为True为流式输出
    )

    # 4. 获取大模型响应的数据
    ai_response = response.choices[0].message.content
    print("<---------- AI大模型响应数据")

    # 5. 更新消息列表中的消息
    if is_initial_prompt:
        session_data["message"] = [{"role": "assistant", "content": ai_response}]
    else:
        messages.pop(0) # 删除系统提示词
        messages.append({"role": "assistant", "content": ai_response})
        session_data["message"] = messages
    print("------> 更新后的会话信息")

    # 6. 保存会话信息到json文件中
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    # 7. 返回数据
    return ApiResponse(code=200, message="请求成功", data=ai_response)

# 统一处理异常，捕获所有异常
@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    print(f"处理异常，请求路径：{request.url}, 捕获异常: {exc}")
    return JSONResponse(content={"code": 500, "message": "服务器内部错误", "data": None})




#  启动服务 ----> uvicorn：python 中的轻量级web服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
