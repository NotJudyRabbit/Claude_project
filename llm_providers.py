"""
多 LLM 提供商抽象层
支持 Claude (Anthropic) / OpenAI / DeepSeek / 通义千问 (Qwen)
"""
import json

PROVIDERS = {
    "claude": {
        "name": "Claude (Anthropic)",
        "models": [
            {"id": "claude-opus-4-6", "name": "Claude Opus 4.6"},
            {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6"},
            {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
        ],
        "key_hint": "ANTHROPIC_API_KEY",
        "key_placeholder": "sk-ant-...",
    },
    "openai": {
        "name": "OpenAI",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        ],
        "key_hint": "OPENAI_API_KEY",
        "key_placeholder": "sk-...",
    },
    "deepseek": {
        "name": "DeepSeek",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner"},
        ],
        "base_url": "https://api.deepseek.com",
        "key_hint": "DEEPSEEK_API_KEY",
        "key_placeholder": "sk-...",
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "models": [
            {"id": "qwen-max", "name": "Qwen Max"},
            {"id": "qwen-plus", "name": "Qwen Plus"},
            {"id": "qwen-turbo", "name": "Qwen Turbo"},
        ],
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "key_hint": "DASHSCOPE_API_KEY",
        "key_placeholder": "sk-...",
    },
}


def convert_tools_to_openai(anthropic_tools: list) -> list:
    """将 Anthropic 格式工具定义（input_schema）转换为 OpenAI function calling 格式（parameters）"""
    openai_tools = []
    for tool in anthropic_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return openai_tools


def call_anthropic(model: str, api_key: str, messages: list, tools: list,
                   system_prompt: str, process_tool_fn) -> tuple:
    """
    执行 Anthropic Claude 智能体循环（支持多次工具调用）
    messages: Anthropic 格式消息列表，in-place 修改
    process_tool_fn: callable(name: str, input: dict) -> result: dict
    返回 (final_text, all_tool_calls_made)
    """
    import anthropic as anthropic_sdk

    client = anthropic_sdk.Anthropic(api_key=api_key)
    all_tool_calls = []

    while True:
        create_kwargs = dict(model=model, max_tokens=2048, system=system_prompt, messages=messages)
        if tools:  # Anthropic API 不接受空的 tools 列表
            create_kwargs["tools"] = tools
        response = client.messages.create(**create_kwargs)

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            final_text = ""
            for block in assistant_content:
                if hasattr(block, "text"):
                    final_text = block.text
            return final_text, all_tool_calls

        elif response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result = process_tool_fn(block.name, block.input)
                    all_tool_calls.append({
                        "tool": block.name,
                        "input": block.input,
                        "result": result,
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
            messages.append({"role": "user", "content": tool_results})

        else:
            # 其他停止原因，提取已有文本后返回
            final_text = ""
            for block in assistant_content:
                if hasattr(block, "text"):
                    final_text = block.text
            return final_text, all_tool_calls


def _openai_chat(base_url: str, api_key: str, model: str, messages: list,
                 tools: list = None, timeout: int = 60) -> dict:
    """直接用 requests 调 OpenAI 兼容接口，返回解析后的 dict。"""
    import requests as _req

    # 规范化 base_url：去掉末尾 /，确保以 /v1 结尾
    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"
    endpoint = url + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "max_tokens": 2048, "messages": messages}
    if tools:
        payload["tools"] = tools

    resp = _req.post(endpoint, json=payload, headers=headers, timeout=timeout)
    if not resp.ok:
        raise ValueError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    if "error" in data:
        raise ValueError(f"API 错误: {data['error']}")
    return data


def call_openai_compatible(provider: str, model: str, api_key: str, messages: list,
                            tools: list, system_prompt: str, process_tool_fn,
                            base_url_override: str = None) -> tuple:
    """
    执行 OpenAI 兼容 API 的智能体循环（OpenAI / DeepSeek / Qwen）
    使用 requests 直接调用，避免 SDK 版本兼容问题。
    返回 (final_text, all_tool_calls_made)
    """
    base_url = base_url_override or PROVIDERS.get(provider, {}).get("base_url", "https://api.openai.com/v1")
    openai_tools = convert_tools_to_openai(tools)
    all_tool_calls = []

    while True:
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        data = _openai_chat(base_url, api_key, model, full_messages,
                            tools=openai_tools or None)

        choice = data["choices"][0]
        msg = choice["message"]
        finish_reason = choice.get("finish_reason", "stop")

        # 构造助手消息 dict 并加入持久历史
        assistant_dict = {"role": "assistant", "content": msg.get("content") or ""}
        tool_calls_raw = msg.get("tool_calls") or []
        if tool_calls_raw:
            assistant_dict["tool_calls"] = tool_calls_raw
        messages.append(assistant_dict)

        if finish_reason == "stop" or not tool_calls_raw:
            return msg.get("content") or "", all_tool_calls

        elif finish_reason == "tool_calls":
            for tc in tool_calls_raw:
                fn = tc.get("function", {})
                try:
                    tool_input = json.loads(fn.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    tool_input = {}

                result = process_tool_fn(fn.get("name", ""), tool_input)
                all_tool_calls.append({
                    "tool": fn.get("name", ""),
                    "input": tool_input,
                    "result": result,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps(result, ensure_ascii=False),
                })

        else:
            return msg.get("content") or "", all_tool_calls


def call_llm(provider: str, model: str, api_key: str, messages: list,
             tools: list, system_prompt: str, process_tool_fn,
             base_url: str = None) -> tuple:
    """
    统一 LLM 调用入口，根据 provider 路由到对应实现
    messages: 消息历史列表（格式随 provider 而定），in-place 修改
    process_tool_fn: callable(name: str, input: dict) -> result: dict
    base_url: 可选，覆盖默认 base_url（用于自定义 OpenAI 兼容服务）
    返回 (final_text, all_tool_calls_made)
    """
    # 有自定义 base_url 时，强制走 OpenAI 兼容接口（custom endpoint 几乎都是 OpenAI 格式）
    if base_url:
        return call_openai_compatible(
            provider, model, api_key, messages, tools, system_prompt, process_tool_fn,
            base_url_override=base_url,
        )
    elif provider == "claude":
        return call_anthropic(model, api_key, messages, tools, system_prompt, process_tool_fn)
    elif provider in PROVIDERS:
        return call_openai_compatible(
            provider, model, api_key, messages, tools, system_prompt, process_tool_fn,
        )
    else:
        raise ValueError(f"未知提供商: {provider}")
