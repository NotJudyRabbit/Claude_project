"""
康复管理系统 - SQLite 数据库层
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "rehab_demo.db")

# 种子动作数据（从 agent.py _build_rehab_plan 提取）
SEED_ACTIONS = [
    # 急性期
    {
        "name": "制动休息", "stage": "急性期", "injury_types": "踝关节扭伤,膝关节损伤,骨折",
        "description": "避免负重和剧烈活动", "reps": "持续",
        "precautions": "保持受伤部位制动", "video_url": "", "tags": "急性期,保护"
    },
    {
        "name": "冰敷", "stage": "急性期", "injury_types": "踝关节扭伤,膝关节损伤,肌肉拉伤",
        "description": "每次15-20分钟，每日3-4次", "reps": "每2-3小时一次",
        "precautions": "冰袋包裹毛巾，避免直接接触皮肤", "video_url": "", "tags": "急性期,消炎"
    },
    {
        "name": "踝泵练习", "stage": "急性期", "injury_types": "踝关节扭伤,骨折",
        "description": "卧位，足踝缓慢上下屈伸", "reps": "10次/组，3组/天",
        "precautions": "在无痛或微痛范围内进行", "video_url": "", "tags": "急性期,循环"
    },
    # 亚急性期
    {
        "name": "关节活动度练习", "stage": "亚急性期", "injury_types": "踝关节扭伤,膝关节损伤,肩部损伤",
        "description": "主动缓慢活动受伤关节至最大无痛范围", "reps": "10次/组，3组/天",
        "precautions": "不强行拉伸", "video_url": "", "tags": "亚急性期,活动度"
    },
    {
        "name": "等长收缩练习", "stage": "亚急性期", "injury_types": "肌肉拉伤,韧带损伤",
        "description": "肌肉用力但关节不活动", "reps": "保持5秒，10次/组，3组/天",
        "precautions": "轻微用力即可", "video_url": "", "tags": "亚急性期,肌力"
    },
    {
        "name": "冷热交替浸泡", "stage": "亚急性期", "injury_types": "踝关节扭伤,肌肉拉伤",
        "description": "冷水1分钟 → 热水3分钟，交替3次", "reps": "每日1-2次",
        "precautions": "热水温度不超过40°C", "video_url": "", "tags": "亚急性期,消肿"
    },
    # 恢复期
    {
        "name": "抗阻训练", "stage": "恢复期", "injury_types": "踝关节扭伤,膝关节损伤,肌肉拉伤",
        "description": "弹力带或轻重量进行多方向抗阻练习", "reps": "15次/组，3组/天",
        "precautions": "从轻阻力开始，无痛为原则", "video_url": "", "tags": "恢复期,肌力"
    },
    {
        "name": "本体感觉训练", "stage": "恢复期", "injury_types": "踝关节扭伤,膝关节损伤",
        "description": "单腿站立平衡练习", "reps": "保持30秒，5次/组，2组/天",
        "precautions": "旁边有支撑物保护", "video_url": "", "tags": "恢复期,平衡"
    },
    {
        "name": "功能性动作训练", "stage": "恢复期", "injury_types": "踝关节扭伤,膝关节损伤,腰背部损伤",
        "description": "深蹲、弓步等基础功能动作", "reps": "10次/组，3组/天",
        "precautions": "动作规范，避免代偿", "video_url": "", "tags": "恢复期,功能"
    },
    # 强化期
    {
        "name": "专项力量训练", "stage": "强化期", "injury_types": "踝关节扭伤,膝关节损伤,肩部损伤",
        "description": "针对薄弱肌群进行强化训练", "reps": "8-12次/组，4组/天",
        "precautions": "渐进式超负荷原则", "video_url": "", "tags": "强化期,专项"
    },
    {
        "name": "爆发力训练", "stage": "强化期", "injury_types": "踝关节扭伤,膝关节损伤",
        "description": "跳跃、变向等快速力量练习", "reps": "从低强度开始，逐步提高",
        "precautions": "充分热身后进行", "video_url": "", "tags": "强化期,爆发力"
    },
    {
        "name": "预防性训练", "stage": "强化期", "injury_types": "踝关节扭伤,膝关节损伤,腰背部损伤,肩部损伤",
        "description": "针对受伤部位的预防性强化和柔韧性维护", "reps": "每日10分钟",
        "precautions": "作为常规热身的一部分", "video_url": "", "tags": "强化期,预防"
    },
]

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS patients (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    role            TEXT DEFAULT '学员',
    gender          TEXT,
    age             INTEGER,
    unit            TEXT,
    phone           TEXT,
    injury_description TEXT DEFAULT '',
    recovery_stage  TEXT DEFAULT '未知',
    pain_level      INTEGER,
    notes           TEXT DEFAULT '',
    ai_profile      TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id           TEXT PRIMARY KEY,
    patient_id   INTEGER REFERENCES patients(id) ON DELETE SET NULL,
    patient_name TEXT,
    provider     TEXT DEFAULT 'claude',
    model        TEXT DEFAULT 'claude-sonnet-4-6',
    started_at   TEXT DEFAULT (datetime('now','localtime')),
    ended_at     TEXT
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES chat_sessions(id),
    patient_id  INTEGER REFERENCES patients(id) ON DELETE SET NULL,
    tool_name   TEXT NOT NULL,
    input_json  TEXT,
    result_json TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS rehab_plans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    session_id  TEXT REFERENCES chat_sessions(id),
    injury_type TEXT,
    stage       TEXT,
    severity    TEXT,
    plan_json   TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS feedback_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER REFERENCES patients(id) ON DELETE SET NULL,
    session_id      TEXT REFERENCES chat_sessions(id),
    feedback_type   TEXT,
    content         TEXT,
    pain_change     TEXT,
    risk_level      TEXT,
    action_required TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS actions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    stage       TEXT,
    injury_types TEXT DEFAULT '',
    description TEXT DEFAULT '',
    reps        TEXT DEFAULT '',
    precautions TEXT DEFAULT '',
    video_url   TEXT DEFAULT '',
    tags        TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS system_users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    role        TEXT DEFAULT '学员',
    permissions TEXT DEFAULT '[]',
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript(CREATE_TABLES_SQL)
        # 写入种子动作数据（仅首次）
        count = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
        if count == 0:
            conn.executemany(
                """INSERT INTO actions (name, stage, injury_types, description, reps, precautions, video_url, tags)
                   VALUES (:name, :stage, :injury_types, :description, :reps, :precautions, :video_url, :tags)""",
                SEED_ACTIONS
            )
        # 创建默认管理员用户
        conn.execute(
            "INSERT OR IGNORE INTO system_users (username, role, permissions) VALUES (?, ?, ?)",
            ("admin", "管理员", json.dumps(["查看患者", "编辑患者", "删除患者", "管理动作库", "查看日志", "系统配置"]))
        )
        conn.commit()
        print("Database initialized successfully.")
    finally:
        conn.close()


# ─── 会话管理 ─────────────────────────────────────────────────────────────────

def create_session(session_id: str, provider: str = "claude", model: str = "claude-sonnet-4-6"):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO chat_sessions (id, provider, model) VALUES (?, ?, ?)",
            (session_id, provider, model)
        )
        conn.commit()
    finally:
        conn.close()


def end_session(session_id: str):
    if not session_id:
        return
    conn = get_db()
    try:
        conn.execute(
            "UPDATE chat_sessions SET ended_at = datetime('now','localtime') WHERE id = ?",
            (session_id,)
        )
        conn.commit()
    finally:
        conn.close()


def update_session_patient(session_id: str, patient_id: int, patient_name: str):
    if not session_id:
        return
    conn = get_db()
    try:
        conn.execute(
            "UPDATE chat_sessions SET patient_id = ?, patient_name = ? WHERE id = ?",
            (patient_id, patient_name, session_id)
        )
        conn.commit()
    finally:
        conn.close()


# ─── 患者管理 ─────────────────────────────────────────────────────────────────

def upsert_patient_from_tool(session_id: str, tool_input: dict) -> int:
    """
    save_patient_info 工具触发时写入/更新患者记录。
    先按 session_id 查找已关联的 patient_id，有则更新，无则新建。
    返回 patient_id。
    """
    conn = get_db()
    try:
        # 查找本 session 已关联的患者
        row = conn.execute(
            "SELECT patient_id FROM chat_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        patient_id = row["patient_id"] if row else None

        name = tool_input.get("name", "未知")
        injury_description = tool_input.get("injury_description", "")
        recovery_stage = tool_input.get("recovery_stage", "未知")
        pain_level = tool_input.get("pain_level")
        notes = tool_input.get("notes", "")

        if patient_id:
            conn.execute(
                """UPDATE patients SET name=?, injury_description=?, recovery_stage=?,
                   pain_level=?, notes=?, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (name, injury_description, recovery_stage, pain_level, notes, patient_id)
            )
        else:
            cur = conn.execute(
                """INSERT INTO patients (name, injury_description, recovery_stage, pain_level, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, injury_description, recovery_stage, pain_level, notes)
            )
            patient_id = cur.lastrowid
            conn.execute(
                "UPDATE chat_sessions SET patient_id=?, patient_name=? WHERE id=?",
                (patient_id, name, session_id)
            )

        conn.commit()
        return patient_id
    finally:
        conn.close()


def get_patients(search: str = "", stage: str = "", role: str = "",
                 page: int = 1, per_page: int = 20) -> dict:
    conn = get_db()
    try:
        conditions = []
        params = []
        if search:
            conditions.append("(name LIKE ? OR injury_description LIKE ? OR unit LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        if stage:
            conditions.append("recovery_stage = ?")
            params.append(stage)
        if role:
            conditions.append("role = ?")
            params.append(role)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        total = conn.execute(f"SELECT COUNT(*) FROM patients {where}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT * FROM patients {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "items": [dict(r) for r in rows]
        }
    finally:
        conn.close()


def get_patient(patient_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not row:
            return None
        patient = dict(row)
        # 最近3条方案
        plans = conn.execute(
            "SELECT * FROM rehab_plans WHERE patient_id = ? ORDER BY created_at DESC LIMIT 3",
            (patient_id,)
        ).fetchall()
        patient["rehab_plans"] = [dict(p) for p in plans]
        # 最近5条反馈
        feedbacks = conn.execute(
            "SELECT * FROM feedback_logs WHERE patient_id = ? ORDER BY created_at DESC LIMIT 5",
            (patient_id,)
        ).fetchall()
        patient["feedback_logs"] = [dict(f) for f in feedbacks]
        # 会话列表
        sessions = conn.execute(
            "SELECT * FROM chat_sessions WHERE patient_id = ? ORDER BY started_at DESC LIMIT 5",
            (patient_id,)
        ).fetchall()
        patient["sessions"] = [dict(s) for s in sessions]
        return patient
    finally:
        conn.close()


def create_patient(data: dict) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO patients (name, role, gender, age, unit, phone,
               injury_description, recovery_stage, pain_level, notes)
               VALUES (:name, :role, :gender, :age, :unit, :phone,
               :injury_description, :recovery_stage, :pain_level, :notes)""",
            {
                "name": data.get("name", ""),
                "role": data.get("role", "学员"),
                "gender": data.get("gender"),
                "age": data.get("age"),
                "unit": data.get("unit"),
                "phone": data.get("phone"),
                "injury_description": data.get("injury_description", ""),
                "recovery_stage": data.get("recovery_stage", "未知"),
                "pain_level": data.get("pain_level"),
                "notes": data.get("notes", ""),
            }
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_patient(patient_id: int, data: dict):
    fields = ["name", "role", "gender", "age", "unit", "phone",
              "injury_description", "recovery_stage", "pain_level", "notes", "ai_profile"]
    updates = []
    params = []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return
    updates.append("updated_at = datetime('now','localtime')")
    params.append(patient_id)
    conn = get_db()
    try:
        conn.execute(f"UPDATE patients SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    finally:
        conn.close()


def delete_patient(patient_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
    finally:
        conn.close()


# ─── 康复方案 ─────────────────────────────────────────────────────────────────

def save_rehab_plan(session_id: str, patient_id: int | None, plan: dict):
    if not plan:
        return
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO rehab_plans (patient_id, session_id, injury_type, stage, severity, plan_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                patient_id,
                session_id,
                plan.get("injury_type", ""),
                plan.get("stage", ""),
                plan.get("severity", ""),
                json.dumps(plan, ensure_ascii=False)
            )
        )
        conn.commit()
    finally:
        conn.close()


# ─── 训练反馈 ─────────────────────────────────────────────────────────────────

def log_feedback(session_id: str, patient_id: int | None, fb: dict):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO feedback_logs (patient_id, session_id, feedback_type, content,
               pain_change, risk_level, action_required)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                patient_id,
                session_id,
                fb.get("feedback_type", ""),
                fb.get("content", ""),
                fb.get("pain_change", ""),
                fb.get("risk_level", ""),
                fb.get("action_required", ""),
            )
        )
        conn.commit()
    finally:
        conn.close()


# ─── 工具调用日志 ─────────────────────────────────────────────────────────────

def log_tool_call(session_id: str, patient_id: int | None, name: str, inp: dict, res: dict):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO tool_calls (session_id, patient_id, tool_name, input_json, result_json)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session_id,
                patient_id,
                name,
                json.dumps(inp, ensure_ascii=False),
                json.dumps(res, ensure_ascii=False),
            )
        )
        conn.commit()
    finally:
        conn.close()


# ─── 动作库 ───────────────────────────────────────────────────────────────────

def get_actions(search: str = "", stage: str = "", page: int = 1, per_page: int = 20) -> dict:
    conn = get_db()
    try:
        conditions = []
        params = []
        if search:
            conditions.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        if stage:
            conditions.append("stage = ?")
            params.append(stage)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        total = conn.execute(f"SELECT COUNT(*) FROM actions {where}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT * FROM actions {where} ORDER BY stage, id LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "items": [dict(r) for r in rows]
        }
    finally:
        conn.close()


def get_action(action_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_action(data: dict) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO actions (name, stage, injury_types, description, reps, precautions, video_url, tags)
               VALUES (:name, :stage, :injury_types, :description, :reps, :precautions, :video_url, :tags)""",
            {
                "name": data.get("name", ""),
                "stage": data.get("stage", ""),
                "injury_types": data.get("injury_types", ""),
                "description": data.get("description", ""),
                "reps": data.get("reps", ""),
                "precautions": data.get("precautions", ""),
                "video_url": data.get("video_url", ""),
                "tags": data.get("tags", ""),
            }
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_action(action_id: int, data: dict):
    fields = ["name", "stage", "injury_types", "description", "reps", "precautions", "video_url", "tags"]
    updates = []
    params = []
    for f in fields:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])
    if not updates:
        return
    updates.append("updated_at = datetime('now','localtime')")
    params.append(action_id)
    conn = get_db()
    try:
        conn.execute(f"UPDATE actions SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    finally:
        conn.close()


def delete_action(action_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM actions WHERE id = ?", (action_id,))
        conn.commit()
    finally:
        conn.close()


# ─── 系统用户 ─────────────────────────────────────────────────────────────────

def get_system_users() -> list:
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM system_users ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_system_user(data: dict) -> int:
    conn = get_db()
    try:
        perms = data.get("permissions", [])
        if isinstance(perms, str):
            perms = json.loads(perms)
        cur = conn.execute(
            "INSERT INTO system_users (username, role, permissions) VALUES (?, ?, ?)",
            (data.get("username", ""), data.get("role", "学员"), json.dumps(perms, ensure_ascii=False))
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_system_user(user_id: int, data: dict):
    fields = []
    params = []
    if "role" in data:
        fields.append("role = ?")
        params.append(data["role"])
    if "permissions" in data:
        perms = data["permissions"]
        if isinstance(perms, list):
            perms = json.dumps(perms, ensure_ascii=False)
        fields.append("permissions = ?")
        params.append(perms)
    if not fields:
        return
    params.append(user_id)
    conn = get_db()
    try:
        conn.execute(f"UPDATE system_users SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    finally:
        conn.close()


def delete_system_user(user_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM system_users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# ─── 日志查询 ─────────────────────────────────────────────────────────────────

def get_sessions(page: int = 1, per_page: int = 20) -> dict:
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            "SELECT * FROM chat_sessions ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        ).fetchall()
        return {
            "total": total, "page": page, "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "items": [dict(r) for r in rows]
        }
    finally:
        conn.close()


def get_tool_calls(page: int = 1, per_page: int = 20) -> dict:
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM tool_calls").fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            """SELECT tc.*, p.name as patient_name FROM tool_calls tc
               LEFT JOIN patients p ON tc.patient_id = p.id
               ORDER BY tc.created_at DESC LIMIT ? OFFSET ?""",
            (per_page, offset)
        ).fetchall()
        return {
            "total": total, "page": page, "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "items": [dict(r) for r in rows]
        }
    finally:
        conn.close()


def get_feedback_logs(page: int = 1, per_page: int = 20, risk: str = "") -> dict:
    conn = get_db()
    try:
        conditions = []
        params = []
        if risk:
            conditions.append("fl.risk_level = ?")
            params.append(risk)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        total = conn.execute(f"SELECT COUNT(*) FROM feedback_logs fl {where}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"""SELECT fl.*, p.name as patient_name FROM feedback_logs fl
               LEFT JOIN patients p ON fl.patient_id = p.id
               {where} ORDER BY fl.created_at DESC LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()
        return {
            "total": total, "page": page, "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "items": [dict(r) for r in rows]
        }
    finally:
        conn.close()


# ─── 统计数据 ─────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    conn = get_db()
    try:
        total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]

        high_risk_count = conn.execute(
            "SELECT COUNT(DISTINCT patient_id) FROM feedback_logs WHERE risk_level = '高风险'"
        ).fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")
        today_sessions = conn.execute(
            "SELECT COUNT(*) FROM chat_sessions WHERE started_at LIKE ?",
            (f"{today}%",)
        ).fetchone()[0]

        total_actions = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]

        stage_rows = conn.execute(
            "SELECT recovery_stage, COUNT(*) as cnt FROM patients GROUP BY recovery_stage"
        ).fetchall()
        stage_distribution = {r["recovery_stage"]: r["cnt"] for r in stage_rows}

        injury_rows = conn.execute(
            "SELECT injury_type, COUNT(*) as cnt FROM rehab_plans WHERE injury_type != '' GROUP BY injury_type ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        injury_type_distribution = {r["injury_type"]: r["cnt"] for r in injury_rows}

        recent_rows = conn.execute(
            "SELECT * FROM patients ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        recent_patients = [dict(r) for r in recent_rows]

        return {
            "total_patients": total_patients,
            "high_risk_count": high_risk_count,
            "today_sessions": today_sessions,
            "total_actions": total_actions,
            "stage_distribution": stage_distribution,
            "injury_type_distribution": injury_type_distribution,
            "recent_patients": recent_patients,
        }
    finally:
        conn.close()
