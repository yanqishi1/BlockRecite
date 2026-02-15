import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件（从项目根目录）
# 优先级: 环境变量 > .env 文件 > 硬编码默认值
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

# DeepSeek API 配置（兼容 OpenAI 格式）
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model: Optional[str] = None
) -> Any:
    """
    通用的聊天完成 API 调用

    Args:
        messages: 消息列表，格式 [{"role": "system", "content": "..."}, ...]
        temperature: 温度参数，控制随机性，0-2 之间，默认 0.3
        max_tokens: 最大 tokens 数，默认 2000
        model: 模型名称，默认使用配置的 MODEL

    Returns:
        API 响应对象（openai.types.chat.ChatCompletion）

    Raises:
        Exception: API 调用失败时抛出异常
    """
    req = {
        "model": model or MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    return client.chat.completions.create(**req)


def chat_completion_text(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model: Optional[str] = None
) -> str:
    """
    调用 AI 并返回纯文本响应

    Args:
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 tokens 数
        model: 模型名称

    Returns:
        str: AI 返回的文本内容，失败返回空字符串
    """
    try:
        resp = chat_completion(messages, temperature, max_tokens, model)
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return ""


def chat_completion_json(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model: Optional[str] = None,
    default: Optional[Any] = None
) -> Any:
    """
    调用 AI 并自动解析 JSON 格式响应

    Args:
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 tokens 数
        model: 模型名称
        default: 解析失败时返回的默认值

    Returns:
        dict/list: 解析后的 JSON 数据，失败返回 default
    """
    try:
        resp = chat_completion(messages, temperature, max_tokens, model)
        result_text = (resp.choices[0].message.content or "").strip()
        return _extract_json(result_text)
    except Exception as e:
        print(f"AI JSON 调用失败: {e}")
        return default


def _extract_json(text: str) -> Any:
    """
    从文本中提取并解析 JSON

    支持 markdown 代码块格式和纯 JSON 格式

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        解析后的 JSON 对象，失败返回 None
    """
    json_str = text

    # 处理 markdown 代码块格式
    if '```json' in text:
        json_str = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        json_str = text.split('```')[1].split('```')[0].strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None