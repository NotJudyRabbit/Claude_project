# -*- coding: utf-8 -*-
"""
模拟数据生成脚本
直接写入 SQLite，并通过 API 绑定 session
运行: python seed_data.py
"""
import sqlite3, json, random, sys, os, urllib.request, urllib.error
from datetime import datetime, timedelta

# 解决 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rehab_v2.db")
BASE = "http://localhost:5001"

def api_post(path, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # ─── 清理旧的同名测试数据 ─────────────────────────────────────────
    old = conn.execute("SELECT id FROM patients WHERE name='李建国'").fetchone()
    if old:
        oid = old["id"]
        conn.execute("DELETE FROM training_checkins WHERE patient_id=?", (oid,))
        conn.execute("DELETE FROM teacher_reviews WHERE patient_id=?", (oid,))
        conn.execute("DELETE FROM rehab_plans WHERE patient_id=?", (oid,))
        conn.execute("DELETE FROM patients WHERE id=?", (oid,))
        conn.commit()
        print("已清理旧数据")

    # ─── 1. 插入患者档案 ──────────────────────────────────────────────
    conn.execute("""
        INSERT INTO patients
        (name, role, gender, age, height, weight, unit, phone,
         injury_description, recovery_stage, pain_level,
         medical_history, surgery_history, notes, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'),datetime('now','localtime'))
    """, (
        "李建国","学员","男", 22, 178.0, 72.5,
        "训练一营三连", "13800138001",
        "左膝关节内侧副韧带拉伤，跑步训练急转弯时受伤，局部轻度肿胀",
        "恢复期", 3,
        "2021年右踝关节轻度扭伤，已痊愈", "",
        "每日完成连队体能训练，康复训练安排在晨练后"
    ))
    conn.commit()
    patient_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"✓ 患者档案 已创建 (ID={patient_id})")

    # ─── 1b. 插入一条 session 记录（方案的外键需要） ──────────────────
    seed_sid = "seed-session-001"
    existing_session = conn.execute("SELECT id FROM chat_sessions WHERE id=?", (seed_sid,)).fetchone()
    if not existing_session:
        conn.execute("""
            INSERT INTO chat_sessions (id, patient_id, patient_name, provider, model, started_at)
            VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (seed_sid, patient_id, "李建国", "claude", "claude-sonnet-4-6"))
        conn.commit()

    # ─── 2. 插入康复方案 ──────────────────────────────────────────────
    plan_json = {
        "injury_type": "左膝关节内侧副韧带拉伤",
        "stage": "恢复期",
        "severity": "疼痛评分 3/10",
        "region": "膝关节",
        "目标": "恢复正常膝关节活动度和下肢肌肉力量，提升功能性运动能力，为重返训练场做准备。训练过程中以微痛为界，不强行突破，循序渐进。",
        "原则": "渐进超负荷：逐步增加训练量和强度，注重动作质量，双侧力量均衡",
        "动作": [
            {"名称": "标准深蹲", "说明": "双脚与肩同宽，屈膝下蹲至90度，强化股四头肌和臀部肌群。",
             "次数": "12次×4组，每日1次", "休息": "60秒", "注意": "全脚掌踩地，膝盖不内扣，腰背保持中立位",
             "步骤": "1. 站位准备；2. 缓慢下蹲至90度；3. 维持1秒；4. 有力起身"},
            {"名称": "踏台阶训练", "说明": "单腿踩上台阶，另一腿随后抬起，锻炼平衡和腿部力量。",
             "次数": "每侧12次×3组，每日1次", "休息": "45秒", "注意": "台阶高度从低开始，保持身体垂直",
             "步骤": "1. 站于台阶前；2. 患腿单腿踩上；3. 身体重心转移；4. 缓慢下台"},
            {"名称": "平衡与本体感觉训练", "说明": "单脚站立，训练踝关节本体感觉和稳定性。",
             "次数": "每侧30秒×3组，每日1次", "休息": "30秒", "注意": "旁边备好支撑物，初期可扶墙练习",
             "步骤": "1. 单脚站立；2. 保持平衡30秒；3. 进阶可轻微晃动；4. 双侧交替"},
            {"名称": "弹力带膝关节屈伸", "说明": "使用弹力带进行坐位膝关节屈伸训练，强化股四头肌和腘绳肌。",
             "次数": "15次×3组，每日1次", "休息": "45秒", "注意": "动作缓慢控制，感受肌肉发力，避免弹震",
             "步骤": "1. 坐位弹力带套踝；2. 缓慢伸直膝关节；3. 维持1秒；4. 缓慢屈曲还原"},
            {"名称": "有氧步行训练", "说明": "快步走，提升心肺功能和下肢耐力，为后续跑步训练打基础。",
             "次数": "20-30分钟/次，每周4次", "休息": "隔天进行", "注意": "保持正确步态，出现膝盖疼痛立即停止",
             "步骤": "1. 热身慢走5分钟；2. 加快步速；3. 保持步态自然；4. 放松5分钟"},
        ],
        "禁忌": ["禁止跑步、跳跃等高冲击动作", "避免深蹲超过90度（出现疼痛时）", "不要在疲劳状态下强行训练"],
        "预期时间": "4-8周",
        "说明": "本方案为根据档案信息自动生成的初版方案，经教员王教员审阅确认。",
        "is_auto_generated": True,
    }
    conn.execute("""
        INSERT INTO rehab_plans
        (patient_id, session_id, injury_type, stage, severity, plan_json, status, created_at)
        VALUES (?,?,?,?,?,?,?,datetime('now','-14 days','localtime'))
    """, (
        patient_id, seed_sid,
        "左膝关节内侧副韧带拉伤", "恢复期", "疼痛评分 3/10",
        json.dumps(plan_json, ensure_ascii=False), "已复核"
    ))
    conn.commit()
    conn.commit()
    plan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"✓ 康复方案 已创建 (ID={plan_id})")

    # ─── 3. 插入14天打卡历史 ──────────────────────────────────────────
    exercises_names = ["标准深蹲", "踏台阶训练", "平衡与本体感觉训练", "弹力带膝关节屈伸", "有氧步行训练"]
    scenarios = [
        # (feeling, pain, symptom, completion_bias)
        ("好",  3, "", 0.95),
        ("好",  2, "", 0.95),
        ("一般",3, "训练后膝盖轻微酸痛，休息后缓解", 0.80),
        ("好",  2, "", 1.00),
        ("好",  3, "", 0.90),
        ("好",  2, "", 0.95),
        ("一般",3, "", 0.85),
        ("差",  5, "跑步后膝盖内侧酸胀感明显，冰敷后好转，建议降低训练强度", 0.60),
        ("好",  3, "", 0.90),
        ("一般",2, "久站后膝盖轻微不适", 0.85),
        ("好",  2, "", 1.00),
        ("好",  2, "", 0.95),
        ("好",  2, "", 0.95),
        ("一般",3, "", 0.85),
    ]
    today = datetime.now().date()
    added = 0
    scene_idx = 0
    for i in range(14, 0, -1):
        date = today - timedelta(days=i)
        if date.weekday() == 6:   # 跳过周日
            continue
        if scene_idx >= len(scenarios):
            scene_idx = 0
        feeling, pain, symptom, bias = scenarios[scene_idx]
        scene_idx += 1

        exs = []
        done = 0
        for name in exercises_names:
            ok = random.random() < bias
            if ok: done += 1
            exs.append({"name": name, "completed": ok, "skipped": not ok, "notes": ""})
        rate = round(done / len(exs) * 100)

        conn.execute("""
            INSERT INTO training_checkins
            (patient_id, plan_id, checkin_date, exercises_json, pain_level,
             symptoms, overall_feeling, completion_rate, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            patient_id, plan_id, date.strftime("%Y-%m-%d"),
            json.dumps(exs, ensure_ascii=False),
            pain, symptom, feeling, rate,
            "训练顺利完成" if feeling == "好" else ("今日状态欠佳，已调整强度" if feeling == "差" else ""),
            date.strftime("%Y-%m-%d") + " 09:30:00"
        ))
        added += 1

    conn.commit()
    print(f"✓ 打卡记录 已添加 {added} 条")

    # ─── 4. 插入教员复核记录 ──────────────────────────────────────────
    conn.execute("""
        INSERT INTO teacher_reviews
        (patient_id, plan_id, reviewer_name, review_type, content, suggestion, status, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        patient_id, plan_id, "王教员", "方案复核",
        "已审阅李建国同志的康复训练方案，符合左膝内侧副韧带拉伤恢复期特点，动作选择合理，难度适中，符合部队训练实际情况。",
        "建议增加闭链训练比例，可在踏台阶训练中加入侧向踏步变式，进一步强化膝关节内侧稳定性。冰敷频率可降至训练后1次即可。",
        "已确认", (today - timedelta(days=10)).strftime("%Y-%m-%d 14:00:00")
    ))
    conn.execute("""
        INSERT INTO teacher_reviews
        (patient_id, plan_id, reviewer_name, review_type, content, suggestion, status, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        patient_id, plan_id, "张医官", "阶段评估",
        "对李建国进行第一阶段康复评估：膝关节活动度已恢复至正常范围的90%，肌力测试左右侧差值降至12%，功能评分较入组时提升40分，整体恢复进展良好。",
        "可适时进入强化期训练，建议下周开始加入慢跑训练，起始距离500米，每周递增200米，注意跑姿保护膝关节，避免内翻和过度外旋。",
        "待处理", (today - timedelta(days=3)).strftime("%Y-%m-%d 10:30:00")
    ))
    conn.commit()
    conn.close()
    print("✓ 教员复核 已添加 2 条")

    # ─── 5. 通过 API 绑定 session（使主界面能立即显示该患者） ─────────
    print("\n绑定 session...")
    result = api_post(f"/api/load-patient/{patient_id}", {})
    if result.get("success"):
        print(f"✓ Session 绑定成功 -> {result.get('name')} (ID={patient_id})")
    else:
        print(f"  绑定失败: {result.get('error', '服务未运行')}")
        print(f"  请在浏览器访问: http://localhost:5001/api/load-patient/{patient_id} (POST)")
        print(f"  或直接访问 /profile 页面手动保存一次档案")

    print("\n" + "="*50)
    print("  ✅  模拟数据生成完成！")
    print("="*50)
    print(f"  患者：李建国 (ID={patient_id})")
    print(f"  方案：左膝关节内侧副韧带拉伤 · 恢复期 (ID={plan_id})")
    print(f"  打卡：近14天共 {added} 条记录")
    print(f"  复核：2 条教员复核记录")
    print()
    print("  现在刷新 http://localhost:5001/ 即可查看")
    print("="*50)


if __name__ == "__main__":
    main()
