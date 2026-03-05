"""
康复智能体 Flask 后端
"""
import json
import uuid
import os
import anthropic
from flask import Flask, request, jsonify, render_template
from agent import SYSTEM_PROMPT, TOOLS, process_tool_call
from llm_providers import call_llm, PROVIDERS
import database as db

app = Flask(__name__)
app.secret_key = "rehab_demo_secret_key_2024"

# 全局会话状态（单用户 Demo）
session_state = {
    "patient": None,
    "messages": [],
    "rehab_plan": None,
    "feedback_log": [],
    "session_id": None,
    "patient_id": None,
}


def _ensure_session(provider: str = "claude", model: str = "claude-sonnet-4-6"):
    """确保当前会话已创建 DB 记录"""
    if not session_state["session_id"]:
        sid = str(uuid.uuid4())
        session_state["session_id"] = sid
        db.create_session(sid, provider, model)
    return session_state["session_id"]


def run_agent_turn(user_message: str, api_key: str,
                   provider: str = "claude", model: str = "claude-sonnet-4-6") -> dict:
    """
    执行一轮智能体对话（支持多次工具调用循环）
    返回最终的文本响应和更新后的状态
    """
    session_id = _ensure_session(provider, model)

    session_state["messages"].append({
        "role": "user",
        "content": user_message
    })

    def process_tool(name, inp):
        return process_tool_call(name, inp, session_state)

    final_text, tool_calls_made = call_llm(
        provider, model, api_key,
        session_state["messages"],
        TOOLS,
        SYSTEM_PROMPT,
        process_tool,
    )

    # DB 双写
    patient_id = session_state.get("patient_id")
    for call in tool_calls_made:
        tool_name = call.get("tool", "")
        tool_inp = call.get("input", {})
        tool_res = call.get("result", {})

        if tool_name == "save_patient_info":
            pid = db.upsert_patient_from_tool(session_id, tool_inp)
            session_state["patient_id"] = pid
            patient_id = pid

        elif tool_name == "generate_rehab_plan":
            plan = session_state.get("rehab_plan") or tool_res.get("plan", {})
            db.save_rehab_plan(session_id, patient_id, plan)

        elif tool_name == "log_training_feedback":
            db.log_feedback(session_id, patient_id, tool_inp)

        db.log_tool_call(session_id, patient_id, tool_name, tool_inp, tool_res)

    return {
        "response": final_text,
        "tool_calls": tool_calls_made,
        "patient": session_state["patient"],
        "rehab_plan": session_state["rehab_plan"]
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/teacher")
def teacher():
    return render_template("teacher.html")


@app.route("/api/me", methods=["GET"])
def get_me():
    """获取当前会话患者的完整档案"""
    patient_id = session_state.get("patient_id")
    if patient_id:
        patient = db.get_patient(patient_id)
        if patient:
            return jsonify(patient)
    if session_state.get("patient"):
        return jsonify(session_state["patient"])
    return jsonify(None)


@app.route("/api/me", methods=["POST"])
def update_me():
    """更新（或创建）当前会话患者档案"""
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "姓名不能为空"}), 400

    patient_id = session_state.get("patient_id")
    if patient_id:
        db.update_patient(patient_id, data)
    else:
        patient_id = db.create_patient(data)
        session_state["patient_id"] = patient_id
        sid = session_state.get("session_id")
        if sid:
            db.update_session_patient(sid, patient_id, data.get("name", ""))

    session_state["patient"] = {
        "name": data.get("name", ""),
        "gender": data.get("gender", ""),
        "age": data.get("age"),
        "height": data.get("height"),
        "weight": data.get("weight"),
        "injury_description": data.get("injury_description", ""),
        "recovery_stage": data.get("recovery_stage", "未知"),
        "pain_level": data.get("pain_level"),
        "notes": data.get("notes", ""),
    }
    return jsonify({"success": True, "patient_id": patient_id, "message": "档案已更新"})


@app.route("/models", methods=["GET"])
def get_models():
    """返回所有支持的提供商和模型列表（过滤内部字段）"""
    result = {}
    for pid, pdata in PROVIDERS.items():
        result[pid] = {
            "name": pdata["name"],
            "models": pdata["models"],
            "key_hint": pdata.get("key_hint", "API Key"),
            "key_placeholder": pdata.get("key_placeholder", "sk-..."),
        }
    return jsonify(result)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    api_key = data.get("api_key", "").strip()
    provider = data.get("provider", "claude").strip()
    model = data.get("model", "claude-sonnet-4-6").strip()

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    if not api_key:
        return jsonify({"error": "请输入 API Key"}), 400

    try:
        result = run_agent_turn(user_message, api_key, provider, model)
        return jsonify(result)
    except anthropic.AuthenticationError:
        return jsonify({"error": "API Key 无效，请检查后重试"}), 401
    except anthropic.RateLimitError:
        return jsonify({"error": "请求频率超限，请稍后重试"}), 429
    except Exception as e:
        try:
            import openai
            if isinstance(e, openai.AuthenticationError):
                return jsonify({"error": "API Key 无效，请检查后重试"}), 401
            if isinstance(e, openai.RateLimitError):
                return jsonify({"error": "请求频率超限，请稍后重试"}), 429
        except ImportError:
            pass
        return jsonify({"error": f"请求失败：{str(e)}"}), 500


@app.route("/reset", methods=["POST"])
def reset():
    """重置会话状态"""
    db.end_session(session_state.get("session_id"))

    session_state["patient"] = None
    session_state["messages"] = []
    session_state["rehab_plan"] = None
    session_state["feedback_log"] = []
    session_state["session_id"] = None
    session_state["patient_id"] = None
    return jsonify({"success": True, "message": "会话已重置"})


@app.route("/state", methods=["GET"])
def get_state():
    """获取当前会话状态（用于前端同步）"""
    return jsonify({
        "patient": session_state["patient"],
        "rehab_plan": session_state["rehab_plan"],
        "message_count": len(session_state["messages"])
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 管理端路由
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/admin/api/stats", methods=["GET"])
def admin_stats():
    return jsonify(db.get_stats())


# ─── 患者管理 ─────────────────────────────────────────────────────────────────

@app.route("/admin/api/patients", methods=["GET"])
def admin_patients():
    search = request.args.get("search", "")
    stage = request.args.get("stage", "")
    role = request.args.get("role", "")
    page = int(request.args.get("page", 1))
    return jsonify(db.get_patients(search, stage, role, page))


@app.route("/admin/api/patients", methods=["POST"])
def admin_create_patient():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "姓名不能为空"}), 400
    pid = db.create_patient(data)
    return jsonify({"id": pid, "message": "患者创建成功"})


@app.route("/admin/api/patients/<int:patient_id>", methods=["GET"])
def admin_get_patient(patient_id):
    p = db.get_patient(patient_id)
    if not p:
        return jsonify({"error": "患者不存在"}), 404
    return jsonify(p)


@app.route("/admin/api/patients/<int:patient_id>", methods=["PUT"])
def admin_update_patient(patient_id):
    data = request.get_json() or {}
    db.update_patient(patient_id, data)
    return jsonify({"message": "更新成功"})


@app.route("/admin/api/patients/<int:patient_id>", methods=["DELETE"])
def admin_delete_patient(patient_id):
    db.delete_patient(patient_id)
    return jsonify({"message": "删除成功"})


@app.route("/admin/api/patients/<int:patient_id>/generate-profile", methods=["POST"])
def admin_generate_profile(patient_id):
    """使用 LLM 生成患者 AI 画像"""
    data = request.get_json() or {}
    text = data.get("text", "")
    api_key = data.get("api_key", "")
    provider = data.get("provider", "claude")
    model = data.get("model", "claude-sonnet-4-6")

    if not api_key:
        return jsonify({"error": "请提供 API Key"}), 400

    # 获取患者信息补充上下文
    patient = db.get_patient(patient_id)
    context = ""
    if patient:
        context = f"患者姓名：{patient.get('name', '')}，伤情：{patient.get('injury_description', '')}，阶段：{patient.get('recovery_stage', '')}。"

    prompt = f"""请根据以下康复相关信息，为患者生成一份简洁的综合康复画像（200字以内），包括：伤情特点、当前阶段、康复重点、注意事项。

{context}

补充信息：
{text}

请直接输出画像文字，不要加标题或额外说明。"""

    try:
        if provider == "claude":
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            profile_text = resp.content[0].text
        else:
            # 其他提供商使用 OpenAI 兼容接口
            import openai
            pdata = PROVIDERS.get(provider, {})
            base_url = pdata.get("base_url", "")
            client = openai.OpenAI(api_key=api_key, base_url=base_url if base_url else None)
            resp = client.chat.completions.create(
                model=model,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            profile_text = resp.choices[0].message.content

        db.update_patient(patient_id, {"ai_profile": profile_text})
        return jsonify({"profile": profile_text, "message": "画像生成成功"})

    except Exception as e:
        return jsonify({"error": f"生成失败：{str(e)}"}), 500


# ─── 会话日志 ─────────────────────────────────────────────────────────────────

@app.route("/admin/api/sessions", methods=["GET"])
def admin_sessions():
    page = int(request.args.get("page", 1))
    return jsonify(db.get_sessions(page))


@app.route("/admin/api/tool-calls", methods=["GET"])
def admin_tool_calls():
    page = int(request.args.get("page", 1))
    return jsonify(db.get_tool_calls(page))


@app.route("/admin/api/feedback", methods=["GET"])
def admin_feedback():
    page = int(request.args.get("page", 1))
    risk = request.args.get("risk", "")
    return jsonify(db.get_feedback_logs(page, risk=risk))


# ─── 动作库 ───────────────────────────────────────────────────────────────────

@app.route("/admin/api/actions", methods=["GET"])
def admin_actions():
    search = request.args.get("search", "")
    stage = request.args.get("stage", "")
    page = int(request.args.get("page", 1))
    return jsonify(db.get_actions(search, stage, page))


@app.route("/admin/api/actions", methods=["POST"])
def admin_create_action():
    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "动作名称不能为空"}), 400
    aid = db.create_action(data)
    return jsonify({"id": aid, "message": "动作创建成功"})


@app.route("/admin/api/actions/<int:action_id>", methods=["GET"])
def admin_get_action(action_id):
    a = db.get_action(action_id)
    if not a:
        return jsonify({"error": "动作不存在"}), 404
    return jsonify(a)


@app.route("/admin/api/actions/<int:action_id>", methods=["PUT"])
def admin_update_action(action_id):
    data = request.get_json() or {}
    db.update_action(action_id, data)
    return jsonify({"message": "更新成功"})


@app.route("/admin/api/actions/<int:action_id>", methods=["DELETE"])
def admin_delete_action(action_id):
    db.delete_action(action_id)
    return jsonify({"message": "删除成功"})


# ─── 系统用户 ─────────────────────────────────────────────────────────────────

@app.route("/admin/api/users", methods=["GET"])
def admin_users():
    return jsonify(db.get_system_users())


@app.route("/admin/api/users", methods=["POST"])
def admin_create_user():
    data = request.get_json() or {}
    if not data.get("username"):
        return jsonify({"error": "用户名不能为空"}), 400
    try:
        uid = db.create_system_user(data)
        return jsonify({"id": uid, "message": "用户创建成功"})
    except Exception as e:
        return jsonify({"error": f"创建失败：{str(e)}"}), 400


@app.route("/admin/api/users/<int:user_id>", methods=["PUT"])
def admin_update_user(user_id):
    data = request.get_json() or {}
    db.update_system_user(user_id, data)
    return jsonify({"message": "更新成功"})


@app.route("/admin/api/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    db.delete_system_user(user_id)
    return jsonify({"message": "删除成功"})


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    print("=" * 50)
    print("  训练伤康复智能助手 Demo")
    print(f"  用户端: http://localhost:{port}")
    print(f"  管理端: http://localhost:{port}/admin")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=debug)
