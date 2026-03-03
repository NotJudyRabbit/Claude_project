"""
康复智能体：系统提示词 + Claude Tools 定义
"""

SYSTEM_PROMPT = """你是一名专业的训练伤康复智能助手，服务对象为军事院校学员及教员。

## 你的核心能力：
1. **对话式病情采集** - 通过友好对话了解学员的症状、受伤部位、受伤时间、愈合阶段等信息
2. **医学报告解读** - 将专业医学术语通俗化，让学员易于理解自己的伤情
3. **个性化康复方案生成** - 根据伤情类型和恢复阶段，制定科学的康复训练计划
4. **训练动作指导** - 提供具体动作的体位、组数、次数、注意事项和禁忌
5. **24小时问答支持** - 随时解答学员关于康复训练的疑问

## 工作流程：
1. 首先通过友好的对话收集学员基本信息（姓名、伤情、阶段）
2. 收集到足够信息后，使用 `save_patient_info` 工具保存档案
3. 完成初步评估后，使用 `generate_rehab_plan` 工具生成个性化康复方案
4. 训练过程中如有反馈，使用 `log_training_feedback` 工具记录并评估风险

## 常见训练伤类型：
- **急性损伤**：扭伤、拉伤、骨折（急性期/亚急性期/恢复期）
- **慢性损伤**：应力性骨折、肌腱炎、滑囊炎
- **疲劳性损伤**：过度训练综合征、肌肉疲劳
- **常见部位**：踝关节、膝关节、腰背部、肩部

## 康复阶段划分：
- **急性期**（伤后0-72小时）：以制动保护为主，遵循RICE原则
- **亚急性期**（伤后3-14天）：开始轻度活动，防止肌肉萎缩
- **恢复期**（伤后2-6周）：逐步恢复功能性训练
- **强化期**（伤后6周以上）：专项训练，重返全面训练

## 重要原则：
- 始终强调循序渐进，禁止带伤强训
- 发现高风险情况立即告知教员或医疗人员
- 建议专业医疗诊断，不替代医生诊断
- 用简洁、温暖、专业的语言与学员沟通

## 对话风格：
- 语气亲切专业，像一位关心学员的军医助手
- 信息采集时每次只问1-2个问题，避免学员感到压力
- 给出建议时要具体可操作，避免模糊表述
"""

TOOLS = [
    {
        "name": "save_patient_info",
        "description": "当收集到学员的基本信息（姓名、伤情描述、当前阶段）后，调用此工具保存患者档案。在对话中了解到足够信息时主动调用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "学员姓名"
                },
                "injury_description": {
                    "type": "string",
                    "description": "伤情描述，包括受伤部位、伤情类型、受伤时间"
                },
                "recovery_stage": {
                    "type": "string",
                    "enum": ["急性期", "亚急性期", "恢复期", "强化期", "未知"],
                    "description": "当前康复阶段"
                },
                "pain_level": {
                    "type": "integer",
                    "description": "疼痛程度，1-10分（1=无痛，10=剧烈疼痛）",
                    "minimum": 1,
                    "maximum": 10
                },
                "notes": {
                    "type": "string",
                    "description": "其他备注信息，如既往史、用药情况等"
                }
            },
            "required": ["name", "injury_description", "recovery_stage"]
        }
    },
    {
        "name": "generate_rehab_plan",
        "description": "根据学员的伤情评估结果，生成个性化分阶段康复方案。在完成初步评估并保存患者信息后调用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "injury_type": {
                    "type": "string",
                    "description": "伤情类型，如：踝关节扭伤、膝关节韧带损伤、腰肌劳损等"
                },
                "current_stage": {
                    "type": "string",
                    "enum": ["急性期", "亚急性期", "恢复期", "强化期"],
                    "description": "当前康复阶段"
                },
                "severity": {
                    "type": "string",
                    "enum": ["轻度", "中度", "重度"],
                    "description": "损伤严重程度"
                },
                "special_requirements": {
                    "type": "string",
                    "description": "特殊要求或限制，如：不能负重、必须保持某体位等"
                }
            },
            "required": ["injury_type", "current_stage", "severity"]
        }
    },
    {
        "name": "log_training_feedback",
        "description": "记录学员在康复训练过程中的反馈，评估训练效果和潜在风险。当学员报告训练感受、疼痛变化或异常症状时调用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_type": {
                    "type": "string",
                    "enum": ["训练感受", "疼痛反馈", "进展报告", "异常症状", "求助咨询"],
                    "description": "反馈类型"
                },
                "content": {
                    "type": "string",
                    "description": "反馈内容的详细描述"
                },
                "pain_change": {
                    "type": "string",
                    "enum": ["明显改善", "轻微改善", "无变化", "轻微加重", "明显加重"],
                    "description": "与上次相比疼痛变化情况"
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["低风险", "中风险", "高风险"],
                    "description": "根据症状判断的风险等级"
                },
                "action_required": {
                    "type": "string",
                    "description": "建议采取的行动，如：继续当前方案、调整训练强度、立即就医等"
                }
            },
            "required": ["feedback_type", "content", "risk_level", "action_required"]
        }
    }
]


def process_tool_call(tool_name: str, tool_input: dict, session_state: dict) -> dict:
    """
    处理工具调用，更新会话状态，返回工具结果
    """
    if tool_name == "save_patient_info":
        session_state["patient"] = {
            "name": tool_input.get("name", "未知"),
            "injury_description": tool_input.get("injury_description", ""),
            "recovery_stage": tool_input.get("recovery_stage", "未知"),
            "pain_level": tool_input.get("pain_level"),
            "notes": tool_input.get("notes", "")
        }
        return {
            "success": True,
            "message": f"已成功保存 {tool_input.get('name')} 的患者档案",
            "patient_id": f"PT{hash(tool_input.get('name', '')) % 10000:04d}"
        }

    elif tool_name == "generate_rehab_plan":
        plan = _build_rehab_plan(
            tool_input.get("injury_type", ""),
            tool_input.get("current_stage", ""),
            tool_input.get("severity", "中度"),
            tool_input.get("special_requirements", "")
        )
        session_state["rehab_plan"] = plan
        return {
            "success": True,
            "plan": plan,
            "message": "康复方案已生成"
        }

    elif tool_name == "log_training_feedback":
        if "feedback_log" not in session_state:
            session_state["feedback_log"] = []
        session_state["feedback_log"].append({
            "type": tool_input.get("feedback_type"),
            "content": tool_input.get("content"),
            "pain_change": tool_input.get("pain_change"),
            "risk_level": tool_input.get("risk_level"),
            "action": tool_input.get("action_required")
        })
        return {
            "success": True,
            "risk_level": tool_input.get("risk_level"),
            "action_required": tool_input.get("action_required"),
            "message": "反馈已记录"
        }

    return {"success": False, "message": f"未知工具: {tool_name}"}


def _build_rehab_plan(injury_type: str, stage: str, severity: str, special_req: str) -> dict:
    """根据伤情生成标准化康复方案框架"""
    plans = {
        "急性期": {
            "目标": "控制炎症，减轻疼痛，保护受伤部位",
            "原则": "遵循 RICE 原则（休息、冰敷、加压、抬高）",
            "动作": [
                {"名称": "制动休息", "说明": "避免负重和剧烈活动", "次数": "持续", "注意": "保持受伤部位制动"},
                {"名称": "冰敷", "说明": "每次15-20分钟，每日3-4次", "次数": "每2-3小时一次", "注意": "冰袋包裹毛巾，避免直接接触皮肤"},
                {"名称": "踝泵练习（如适用）", "说明": "卧位，足踝缓慢上下屈伸", "次数": "10次/组，3组/天", "注意": "在无痛或微痛范围内进行"}
            ],
            "禁忌": ["热敷", "按摩受伤部位", "负重行走", "剧烈运动"],
            "预期时间": "3-7天"
        },
        "亚急性期": {
            "目标": "恢复关节活动度，防止肌肉萎缩",
            "原则": "在疼痛允许范围内逐步增加活动",
            "动作": [
                {"名称": "关节活动度练习", "说明": "主动缓慢活动受伤关节至最大无痛范围", "次数": "10次/组，3组/天", "注意": "不强行拉伸"},
                {"名称": "等长收缩练习", "说明": "肌肉用力但关节不活动", "次数": "保持5秒，10次/组，3组/天", "注意": "轻微用力即可"},
                {"名称": "冷热交替浸泡", "说明": "冷水1分钟 → 热水3分钟，交替3次", "次数": "每日1-2次", "注意": "热水温度不超过40°C"}
            ],
            "禁忌": ["高强度抗阻训练", "冲击性运动", "忽视疼痛继续训练"],
            "预期时间": "1-2周"
        },
        "恢复期": {
            "目标": "恢复肌肉力量和功能性动作",
            "原则": "循序渐进增加负荷，强调本体感觉训练",
            "动作": [
                {"名称": "抗阻训练", "说明": "弹力带或轻重量进行多方向抗阻练习", "次数": "15次/组，3组/天", "注意": "从轻阻力开始，无痛为原则"},
                {"名称": "本体感觉训练", "说明": "单腿站立平衡练习", "次数": "保持30秒，5次/组，2组/天", "注意": "旁边有支撑物保护"},
                {"名称": "功能性动作训练", "说明": "深蹲、弓步等基础功能动作", "次数": "10次/组，3组/天", "注意": "动作规范，避免代偿"}
            ],
            "禁忌": ["过度训练", "忽视疼痛信号", "跳跃着地等高冲击动作"],
            "预期时间": "2-4周"
        },
        "强化期": {
            "目标": "重建专项运动能力，预防再损伤",
            "原则": "专项训练结合预防性练习",
            "动作": [
                {"名称": "专项力量训练", "说明": "针对薄弱肌群进行强化训练", "次数": "8-12次/组，4组/天", "注意": "渐进式超负荷原则"},
                {"名称": "爆发力训练", "说明": "跳跃、变向等快速力量练习", "次数": "从低强度开始，逐步提高", "注意": "充分热身后进行"},
                {"名称": "预防性训练", "说明": "针对受伤部位的预防性强化和柔韧性维护", "次数": "每日10分钟", "注意": "作为常规热身的一部分"}
            ],
            "禁忌": ["过度自信忽视保护", "跳过热身直接高强度训练"],
            "预期时间": "4-8周"
        }
    }

    base_plan = plans.get(stage, plans["恢复期"])
    return {
        "injury_type": injury_type,
        "stage": stage,
        "severity": severity,
        "special_requirements": special_req,
        **base_plan
    }
