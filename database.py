"""
康复管理系统 v2 - SQLite 数据库层
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "rehab_v2.db")

# 种子动作数据
SEED_ACTIONS = [
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
    height          REAL,
    weight          REAL,
    unit            TEXT,
    phone           TEXT,
    medical_history TEXT DEFAULT '',
    surgery_history TEXT DEFAULT '',
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
    status      TEXT DEFAULT '待复核',
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

CREATE TABLE IF NOT EXISTS training_checkins (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    plan_id         INTEGER REFERENCES rehab_plans(id) ON DELETE SET NULL,
    checkin_date    TEXT DEFAULT (date('now','localtime')),
    exercises_json  TEXT DEFAULT '[]',
    pain_level      INTEGER,
    symptoms        TEXT DEFAULT '',
    overall_feeling TEXT DEFAULT '一般',
    completion_rate INTEGER DEFAULT 0,
    notes           TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS teacher_reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    plan_id         INTEGER REFERENCES rehab_plans(id) ON DELETE SET NULL,
    reviewer_name   TEXT DEFAULT '',
    review_type     TEXT DEFAULT '方案复核',
    content         TEXT DEFAULT '',
    suggestion      TEXT DEFAULT '',
    status          TEXT DEFAULT '待处理',
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

CREATE TABLE IF NOT EXISTS system_config (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL DEFAULT '',
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    file_size   INTEGER DEFAULT 0,
    file_path   TEXT DEFAULT '',
    content_text TEXT DEFAULT '',
    chunk_count INTEGER DEFAULT 0,
    tags        TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
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
        # 迁移：为旧数据库添加新列
        for col in ["height REAL", "weight REAL",
                    "medical_history TEXT DEFAULT ''",
                    "surgery_history TEXT DEFAULT ''"]:
            try:
                conn.execute(f"ALTER TABLE patients ADD COLUMN {col}")
            except Exception:
                pass
        try:
            conn.execute("ALTER TABLE rehab_plans ADD COLUMN status TEXT DEFAULT '待复核'")
        except Exception:
            pass
        # 迁移：确保 system_config 表存在（旧数据库兼容）
        conn.execute("""CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()
        # 写入种子动作数据（仅首次）
        count = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
        if count == 0:
            conn.executemany(
                """INSERT INTO actions (name, stage, injury_types, description, reps, precautions, video_url, tags)
                   VALUES (:name, :stage, :injury_types, :description, :reps, :precautions, :video_url, :tags)""",
                SEED_ACTIONS
            )
        conn.execute(
            "INSERT OR IGNORE INTO system_users (username, role, permissions) VALUES (?, ?, ?)",
            ("admin", "管理员", json.dumps(["查看患者", "编辑患者", "删除患者", "管理动作库", "查看日志", "系统配置"]))
        )
        conn.commit()
        print("Database initialized successfully.")
    finally:
        conn.close()
    # 确保演示数据存在
    ensure_seed_patient()


def ensure_seed_patient() -> int:
    """
    幂等地确保李建国演示数据存在于数据库，每次启动均调用。
    若已存在则只更新 session 绑定记录；若不存在则完整插入。
    返回 patient_id。
    """
    from datetime import datetime, timedelta
    import random

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM patients WHERE name='李建国' ORDER BY id LIMIT 1"
        ).fetchone()

        if row:
            # 已有数据，直接返回 id
            return row["id"]

        # ── 插入患者档案 ──────────────────────────────────────────
        conn.execute("""
            INSERT INTO patients
              (name, role, gender, age, height, weight, unit, phone,
               injury_description, recovery_stage, pain_level,
               medical_history, surgery_history, notes,
               created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                    datetime('now','localtime'),datetime('now','localtime'))
        """, (
            "李建国", "学员", "男", 22, 178.0, 72.5,
            "训练一营三连", "13800138001",
            "左膝关节内侧副韧带拉伤，跑步训练急转弯时受伤，局部轻度肿胀",
            "恢复期", 3,
            "2021年右踝关节轻度扭伤，已痊愈", "",
            "每日完成连队体能训练，康复训练安排在晨练后",
        ))
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # ── 插入 session 记录（plan 外键需要）────────────────────
        seed_sid = f"seed-session-{pid}"
        conn.execute("""
            INSERT OR IGNORE INTO chat_sessions
              (id, patient_id, patient_name, provider, model, started_at)
            VALUES (?,?,?,?,?,datetime('now','localtime'))
        """, (seed_sid, pid, "李建国", "claude", "claude-sonnet-4-6"))
        conn.commit()

        # ── 插入康复方案 ──────────────────────────────────────────
        plan_json = {
            "injury_type": "左膝关节内侧副韧带拉伤",
            "stage": "恢复期",
            "severity": "疼痛评分 3/10",
            "region": "膝关节",
            "目标": "恢复正常膝关节活动度和下肢肌肉力量，提升功能性运动能力，为重返训练场做准备。训练过程中以微痛为界，不强行突破，循序渐进。",
            "原则": "渐进超负荷：逐步增加训练量和强度，注重动作质量，双侧力量均衡",
            "动作": [
                {
                    "名称": "标准深蹲",
                    "说明": "双脚与肩同宽，屈膝下蹲至90度，强化股四头肌和臀部肌群。",
                    "次数": "12次×4组，每日1次", "休息": "60秒",
                    "注意": "全脚掌踩地，膝盖不内扣，腰背保持中立位",
                    "步骤": "1. 站位准备；2. 缓慢下蹲至90度；3. 维持1秒；4. 有力起身",
                },
                {
                    "名称": "踏台阶训练",
                    "说明": "单腿踩上台阶，另一腿随后抬起，锻炼平衡和腿部力量。",
                    "次数": "每侧12次×3组，每日1次", "休息": "45秒",
                    "注意": "台阶高度从低开始，保持身体垂直",
                    "步骤": "1. 站于台阶前；2. 患腿单腿踩上；3. 身体重心转移；4. 缓慢下台",
                },
                {
                    "名称": "平衡与本体感觉训练",
                    "说明": "单脚站立，训练踝关节本体感觉和稳定性。",
                    "次数": "每侧30秒×3组，每日1次", "休息": "30秒",
                    "注意": "旁边备好支撑物，初期可扶墙练习",
                    "步骤": "1. 单脚站立；2. 保持平衡30秒；3. 进阶可轻微晃动；4. 双侧交替",
                },
                {
                    "名称": "弹力带膝关节屈伸",
                    "说明": "使用弹力带进行坐位膝关节屈伸训练，强化股四头肌和腘绳肌。",
                    "次数": "15次×3组，每日1次", "休息": "45秒",
                    "注意": "动作缓慢控制，感受肌肉发力，避免弹震",
                    "步骤": "1. 坐位弹力带套踝；2. 缓慢伸直膝关节；3. 维持1秒；4. 缓慢屈曲还原",
                },
                {
                    "名称": "有氧步行训练",
                    "说明": "快步走，提升心肺功能和下肢耐力，为后续跑步训练打基础。",
                    "次数": "20-30分钟/次，每周4次", "休息": "隔天进行",
                    "注意": "保持正确步态，出现膝盖疼痛立即停止",
                    "步骤": "1. 热身慢走5分钟；2. 加快步速；3. 保持步态自然；4. 放松5分钟",
                },
            ],
            "禁忌": ["禁止跑步、跳跃等高冲击动作", "避免深蹲超过90度（出现疼痛时）", "不要在疲劳状态下强行训练"],
            "预期时间": "4-8周",
            "is_auto_generated": True,
        }
        conn.execute("""
            INSERT INTO rehab_plans
              (patient_id, session_id, injury_type, stage, severity, plan_json, status, created_at)
            VALUES (?,?,?,?,?,?,?,datetime('now','-14 days','localtime'))
        """, (
            pid, seed_sid,
            "左膝关节内侧副韧带拉伤", "恢复期", "疼痛评分 3/10",
            json.dumps(plan_json, ensure_ascii=False), "已复核",
        ))
        conn.commit()
        plan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # ── 插入14天打卡历史 ──────────────────────────────────────
        exercise_names = ["标准深蹲", "踏台阶训练", "平衡与本体感觉训练", "弹力带膝关节屈伸", "有氧步行训练"]
        scenarios = [
            ("好", 3, "", 0.95), ("好", 2, "", 0.95),
            ("一般", 3, "训练后膝盖轻微酸痛，休息后缓解", 0.80),
            ("好", 2, "", 1.00), ("好", 3, "", 0.90), ("好", 2, "", 0.95),
            ("一般", 3, "", 0.85),
            ("差", 5, "跑步后膝盖内侧酸胀感明显，冰敷后好转，建议降低训练强度", 0.60),
            ("好", 3, "", 0.90), ("一般", 2, "久站后膝盖轻微不适", 0.85),
            ("好", 2, "", 1.00), ("好", 2, "", 0.95),
            ("好", 2, "", 0.95), ("一般", 3, "", 0.85),
        ]
        today = datetime.now().date()
        rng = random.Random(42)   # 固定种子保证可重现
        si = 0
        for i in range(14, 0, -1):
            date = today - timedelta(days=i)
            if date.weekday() == 6:   # 跳过周日
                continue
            feeling, pain, symptom, bias = scenarios[si % len(scenarios)]
            si += 1
            exs = []
            done = 0
            for name in exercise_names:
                ok = rng.random() < bias
                if ok:
                    done += 1
                exs.append({"name": name, "completed": ok, "skipped": not ok, "notes": ""})
            rate = round(done / len(exercise_names) * 100)
            conn.execute("""
                INSERT INTO training_checkins
                  (patient_id, plan_id, checkin_date, exercises_json, pain_level,
                   symptoms, overall_feeling, completion_rate, notes, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                pid, plan_id, date.strftime("%Y-%m-%d"),
                json.dumps(exs, ensure_ascii=False),
                pain, symptom, feeling, rate,
                "训练顺利完成" if feeling == "好" else ("今日状态欠佳" if feeling == "差" else ""),
                date.strftime("%Y-%m-%d") + " 09:30:00",
            ))
        conn.commit()

        # ── 插入教员复核记录 ──────────────────────────────────────
        conn.execute("""
            INSERT INTO teacher_reviews
              (patient_id, plan_id, reviewer_name, review_type, content, suggestion, status, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            pid, plan_id, "王教员", "方案复核",
            "已审阅李建国同志的康复训练方案，符合左膝内侧副韧带拉伤恢复期特点，动作选择合理，难度适中。",
            "建议增加闭链训练比例，可在踏台阶训练中加入侧向踏步变式，进一步强化膝关节内侧稳定性。",
            "已确认", (today - timedelta(days=10)).strftime("%Y-%m-%d 14:00:00"),
        ))
        conn.execute("""
            INSERT INTO teacher_reviews
              (patient_id, plan_id, reviewer_name, review_type, content, suggestion, status, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            pid, plan_id, "张医官", "阶段评估",
            "膝关节活动度已恢复至正常范围的90%，肌力测试左右侧差值降至12%，功能评分较入组时提升40分，整体恢复进展良好。",
            "可适时进入强化期训练，建议下周开始加入慢跑，起始500米，每周递增200米。",
            "待处理", (today - timedelta(days=3)).strftime("%Y-%m-%d 10:30:00"),
        ))
        conn.commit()
        return pid
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
    conn = get_db()
    try:
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
        plans = conn.execute(
            "SELECT * FROM rehab_plans WHERE patient_id = ? ORDER BY created_at DESC LIMIT 3",
            (patient_id,)
        ).fetchall()
        patient["rehab_plans"] = [dict(p) for p in plans]
        feedbacks = conn.execute(
            "SELECT * FROM feedback_logs WHERE patient_id = ? ORDER BY created_at DESC LIMIT 5",
            (patient_id,)
        ).fetchall()
        patient["feedback_logs"] = [dict(f) for f in feedbacks]
        checkins = conn.execute(
            "SELECT * FROM training_checkins WHERE patient_id = ? ORDER BY created_at DESC LIMIT 5",
            (patient_id,)
        ).fetchall()
        patient["checkins"] = [dict(c) for c in checkins]
        reviews = conn.execute(
            "SELECT * FROM teacher_reviews WHERE patient_id = ? ORDER BY created_at DESC LIMIT 5",
            (patient_id,)
        ).fetchall()
        patient["reviews"] = [dict(r) for r in reviews]
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
            """INSERT INTO patients (name, role, gender, age, height, weight, unit, phone,
               medical_history, surgery_history, injury_description, recovery_stage, pain_level, notes)
               VALUES (:name, :role, :gender, :age, :height, :weight, :unit, :phone,
               :medical_history, :surgery_history, :injury_description, :recovery_stage, :pain_level, :notes)""",
            {
                "name": data.get("name", ""),
                "role": data.get("role", "学员"),
                "gender": data.get("gender"),
                "age": data.get("age"),
                "height": data.get("height"),
                "weight": data.get("weight"),
                "unit": data.get("unit"),
                "phone": data.get("phone"),
                "medical_history": data.get("medical_history", ""),
                "surgery_history": data.get("surgery_history", ""),
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
    fields = ["name", "role", "gender", "age", "height", "weight", "unit", "phone",
              "medical_history", "surgery_history", "injury_description", "recovery_stage",
              "pain_level", "notes", "ai_profile"]
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


def get_latest_plan(patient_id: int) -> dict | None:
    """获取患者最新康复方案"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM rehab_plans WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1",
            (patient_id,)
        ).fetchone()
        if not row:
            return None
        plan = dict(row)
        try:
            plan["plan"] = json.loads(plan.get("plan_json") or "{}")
        except Exception:
            plan["plan"] = {}
        return plan
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


# ─── 训练打卡 ─────────────────────────────────────────────────────────────────

def create_checkin(patient_id: int, data: dict) -> int:
    conn = get_db()
    try:
        exercises = data.get("exercises", [])
        total = len(exercises)
        done = sum(1 for e in exercises if e.get("completed"))
        completion_rate = int(done / total * 100) if total > 0 else 0

        cur = conn.execute(
            """INSERT INTO training_checkins
               (patient_id, plan_id, checkin_date, exercises_json, pain_level,
                symptoms, overall_feeling, completion_rate, notes)
               VALUES (?, ?, date('now','localtime'), ?, ?, ?, ?, ?, ?)""",
            (
                patient_id,
                data.get("plan_id"),
                json.dumps(exercises, ensure_ascii=False),
                data.get("pain_level"),
                data.get("symptoms", ""),
                data.get("overall_feeling", "一般"),
                completion_rate,
                data.get("notes", ""),
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_patient_checkins(patient_id: int, limit: int = 20) -> list:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM training_checkins WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
            (patient_id, limit)
        ).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            try:
                item["exercises"] = json.loads(item.get("exercises_json") or "[]")
            except Exception:
                item["exercises"] = []
            result.append(item)
        return result
    finally:
        conn.close()


# ─── 教员复核 ─────────────────────────────────────────────────────────────────

def create_teacher_review(data: dict) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO teacher_reviews
               (patient_id, plan_id, reviewer_name, review_type, content, suggestion, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("patient_id"),
                data.get("plan_id"),
                data.get("reviewer_name", ""),
                data.get("review_type", "方案复核"),
                data.get("content", ""),
                data.get("suggestion", ""),
                data.get("status", "待处理"),
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_patient_reviews(patient_id: int) -> list:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM teacher_reviews WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_review_status(review_id: int, status: str):
    conn = get_db()
    try:
        conn.execute("UPDATE teacher_reviews SET status = ? WHERE id = ?", (status, review_id))
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


# ─── 系统配置 ─────────────────────────────────────────────────────────────────

def get_system_config() -> dict:
    """获取全部系统配置键值"""
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM system_config").fetchall()
        return {r["key"]: r["value"] for r in rows}
    finally:
        conn.close()


def set_system_config(key: str, value: str):
    """设置单个系统配置项（upsert）"""
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO system_config (key, value, updated_at)
               VALUES (?, ?, datetime('now','localtime'))
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value)
        )
        conn.commit()
    finally:
        conn.close()


def set_system_config_batch(data: dict):
    """批量设置系统配置"""
    conn = get_db()
    try:
        for key, value in data.items():
            conn.execute(
                """INSERT INTO system_config (key, value, updated_at)
                   VALUES (?, ?, datetime('now','localtime'))
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, str(value))
            )
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

        today_checkins = conn.execute(
            "SELECT COUNT(*) FROM training_checkins WHERE checkin_date = ?",
            (today,)
        ).fetchone()[0]

        total_actions = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]

        pending_reviews = conn.execute(
            "SELECT COUNT(*) FROM teacher_reviews WHERE status = '待处理'"
        ).fetchone()[0]

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
            "today_checkins": today_checkins,
            "total_actions": total_actions,
            "pending_reviews": pending_reviews,
            "stage_distribution": stage_distribution,
            "injury_type_distribution": injury_type_distribution,
            "recent_patients": recent_patients,
        }
    finally:
        conn.close()


# ─── 知识库 CRUD ───────────────────────────────────────────────────────────────

def kb_add_item(title: str, filename: str, file_type: str, file_size: int,
                file_path: str, content_text: str, tags: str = "", description: str = "") -> int:
    """插入知识条目，返回 id"""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO knowledge_items
              (title, filename, file_type, file_size, file_path, content_text, tags, description)
            VALUES (?,?,?,?,?,?,?,?)
        """, (title, filename, file_type, file_size, file_path, content_text, tags, description))
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()


def kb_add_chunks(item_id: int, chunks: list[str]):
    """批量插入文本块"""
    conn = get_db()
    try:
        conn.execute("DELETE FROM knowledge_chunks WHERE item_id=?", (item_id,))
        conn.executemany(
            "INSERT INTO knowledge_chunks (item_id, chunk_index, content) VALUES (?,?,?)",
            [(item_id, i, c) for i, c in enumerate(chunks)]
        )
        conn.execute("UPDATE knowledge_items SET chunk_count=? WHERE id=?", (len(chunks), item_id))
        conn.commit()
    finally:
        conn.close()


def kb_list_items() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, title, filename, file_type, file_size, chunk_count, tags, description, created_at
            FROM knowledge_items ORDER BY created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def kb_get_item(item_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM knowledge_items WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def kb_delete_item(item_id: int) -> str | None:
    """删除条目及其分块，返回 file_path 供调用者删磁盘文件"""
    conn = get_db()
    try:
        row = conn.execute("SELECT file_path FROM knowledge_items WHERE id=?", (item_id,)).fetchone()
        file_path = row["file_path"] if row else None
        conn.execute("DELETE FROM knowledge_chunks WHERE item_id=?", (item_id,))
        conn.execute("DELETE FROM knowledge_items WHERE id=?", (item_id,))
        conn.commit()
        return file_path
    finally:
        conn.close()


def kb_search(query: str, top_k: int = 5) -> list[dict]:
    """
    BM25 检索：对所有 knowledge_chunks 做相关性排序，返回 top_k 结果。
    每条结果含 item_id, item_title, chunk_index, content, score。
    """
    import jieba
    from rank_bm25 import BM25Okapi

    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT kc.id, kc.item_id, kc.chunk_index, kc.content, ki.title, ki.file_type, ki.tags
            FROM knowledge_chunks kc
            JOIN knowledge_items ki ON ki.id = kc.item_id
        """).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    # 分词
    tokenized_corpus = [list(jieba.cut(r["content"])) for r in rows]
    tokenized_query  = list(jieba.cut(query))

    bm25   = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenized_query)

    # 排序取 top_k
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    results = []
    for idx, score in indexed:
        if score <= 0:
            continue
        r = rows[idx]
        results.append({
            "item_id":     r["item_id"],
            "item_title":  r["title"],
            "file_type":   r["file_type"],
            "chunk_index": r["chunk_index"],
            "content":     r["content"],
            "category":    r["tags"],
            "score":       round(float(score), 4),
        })
    return results
