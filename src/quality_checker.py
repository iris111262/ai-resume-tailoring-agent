SKILL_SYNONYMS = {
    "Machine Learning": ["machine learning", "ml", "机器学习", "模型训练", "模型调优"],
    "Business Analysis": [
        "business analysis", "business", "商业分析", "业务分析", "需求分析",
        "决策支持", "业务场景", "用户体验", "市场响应", "产品匹配",
    ],
    "Commercial Operations": [
        "commercial operations", "商业运营", "商业化运营", "国际业务", "海外业务",
        "全球市场", "市场拓展", "渠道优化", "商用方向",
    ],
    "Product Management": [
        "product management", "产品管理", "产品规划", "产品策略", "产品设计",
        "产品需求", "产品及渠道", "用户需求",
    ],
    "Python": ["python", "pandas", "numpy"],
    "SQL": ["sql", "数据库"],
    "NLP": ["nlp", "llm", "大模型", "自然语言处理", "关键词提取"],
    "Project Management": [
        "project management", "项目管理", "项目规划", "项目推进", "项目执行",
        "timeline", "milestone", "交付", "进度",
    ],
    "Communication": [
        "communication", "沟通", "跨团队", "stakeholder", "协调", "协作",
    ],
    "English": [
        "english", "英语", "英语流利", "工作语言", "跨文化", "国际视野",
    ],
    "Risk Management": [
        "risk management", "风险管理", "风险评估", "风险控制", "缓解计划",
    ],
    "Resource Planning": [
        "resource planning", "resource allocation", "资源规划", "资源分配", "预算",
    ],
}

ROLE_OPTIONAL_SKILLS = {
    "ml_engineer": {"Business Analysis"},
    "ai_app_engineer": {"Business Analysis"},
    "commercial_ops": {"Product Management"},
}


def check_resume_quality(resume_text: str, jd_info: dict) -> list[str]:
    findings = []
    text = resume_text.lower()
    role = jd_info.get("role", "")
    optional_skills = ROLE_OPTIONAL_SKILLS.get(role, set())

    for skill in jd_info.get("must_have_skills", []):
        if skill in optional_skills:
            continue
        aliases = SKILL_SYNONYMS.get(skill, [skill.lower()])
        if not any(alias.lower() in text for alias in aliases):
            findings.append(f"Missing keyword: {skill}")

    weak_phrases = [
        "responsible for",
        "participated in",
        "assisted with",
        "负责",
        "参与了",
        "协助",
    ]
    for phrase in weak_phrases:
        if phrase in text:
            findings.append(f"Weak bullet detected: {phrase}")

    repeated_concepts = ["dashboard", "reporting", "sql", "python", "analysis", "数据分析"]
    for concept in repeated_concepts:
        count = text.count(concept)
        threshold = 5 if role == "commercial_ops" and concept == "数据分析" else 4
        if count >= threshold:
            findings.append(f"Repeated concept: {concept} appears {count} times")

    if not findings:
        findings.append("No obvious issues detected by rule-based quality check")

    return findings
