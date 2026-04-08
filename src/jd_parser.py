import re

STOP_TERMS = {
    "the", "and", "for", "with", "you", "have", "will", "are", "our",
    "job", "description", "required", "responsibilities", "requirements",
    "task", "tasks", "int", "etc", "plus", "apply", "share", "full", "time",
    "now", "good", "strong", "preferred", "work", "role",
    "岗位职责", "任职要求", "加分项", "毕业时间", "招聘截止日期",
    "本科", "应届", "职位描述", "相关工作", "掌握", "具备", "能力", "经验",
    "要求", "优先", "相关", "工作语言", "海内外", "团队", "感兴趣",
    "planning", "tool", "use", "tools",
}


def normalize_jd_text(jd_text: str) -> str:
    return (
        jd_text.lower()
        .replace("a!", "ai")
        .replace("a1", "ai")
        .replace("大语言模型", "llm")
        .replace("机器学习算法", "machine learning algorithm")
    )


def parse_jd_info(jd_text: str, role: str = "") -> dict:
    text = normalize_jd_text(jd_text)

    skill_map = {
        "SQL": ["sql", "mysql", "postgresql", "数据库"],
        "Python": ["python", "pandas", "numpy", "编码"],
        "A/B Testing": ["a/b", "ab test", "experiment", "实验"],
        "Tableau": ["tableau"],
        "Power BI": ["power bi"],
        "Excel": ["excel", "vlookup", "数据报表"],
        "Machine Learning": ["machine learning", "xgboost", "random forest", "机器学习", "人工智能", "ai", "算法"],
        "PySpark": ["pyspark", "spark", "大数据"],
        "Kafka": ["kafka"],
        "Dashboard": ["dashboard", "visualization", "可视化", "仪表盘"],
        "Business Analysis": ["business", "stakeholder", "insight", "业务", "需求分析", "市场需求", "海外市场", "市场开拓", "渠道"],
        "NLP": ["nlp", "llm", "prompt", "大模型", "大语言模型"],
        "Product Management": ["product", "产品", "产品经理", "产品规划", "功能设计"],
        "Commercial Operations": ["商业化运营", "商业化设计", "商业运营产品", "游戏商业化", "运营", "国际业务", "海外业务", "国际化业务", "商用方向"],
        "AI Product Operations": ["ai工具产品运营", "aigc", "ai产品", "创意模版", "ugc", "社媒", "海外社交媒体"],
        "Quality Management": ["质量", "质量管理", "质量方向", "质量阀", "质量改进", "市场质量"],
        "Project Management": ["project manager", "project management", "program manager", "pjm", "pmp", "项目经理", "项目管理", "项目规划"],
        "Risk Management": ["risk", "风险", "风险管理", "缓解计划"],
        "Resource Planning": ["resource", "资源分配", "资源管理", "预算"],
        "Communication": ["沟通", "协调", "cross-functional", "跨团队", "客户"],
        "English": ["english", "英语", "听说读写", "工作语言", "跨文化", "国际化"],
    }

    focus_map = {
        "analysis": ["analysis", "insight", "kpi", "分析", "洞察"],
        "dashboard": ["dashboard", "visualization", "可视化", "仪表盘"],
        "experiment": ["a/b", "experiment", "测试", "实验"],
        "pipeline": ["etl", "pipeline", "spark", "流程", "数据管理"],
        "ml": ["model", "ml", "机器学习", "人工智能", "ai"],
        "product": ["product", "consumer", "产品", "需求", "功能设计", "产品规划"],
        "operations": ["operations", "运营", "商业化", "商业运营", "调优", "问卷"],
        "content_ops": ["内容", "创意", "模版", "ugc", "社媒", "传播率", "点击率", "成功率"],
        "quality_ops": ["质量", "评审", "闭环", "预警", "纠正措施", "质量改进", "风险评估", "质量阀", "监控"],
        "market": ["market", "市场", "竞品", "海外市场", "本地化", "国际业务", "商用"],
        "collaboration": ["collaboration", "stakeholder", "沟通", "协调", "跨团队", "客户"],
        "planning": ["planning", "plan", "timeline", "milestone", "项目规划", "时间表", "进度"],
        "delivery": ["deliverable", "execution", "监控", "报告", "交付", "推进", "实施"],
        "risk_control": ["risk", "风险", "quality", "质量保证", "质量控制", "缓解计划"],
        "global_ops": ["国际化", "海外", "跨文化", "global", "international", "工作语言"],
    }

    must_have = [k for k, v in skill_map.items() if any(p in text for p in v)]
    focus = [k for k, v in focus_map.items() if any(p in text for p in v)]

    words = re.findall(r"[a-zA-Z]{3,}", text)
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,}", jd_text)
    freq = {}
    for w in words:
        if w not in STOP_TERMS and len(w) >= 3:
            freq[w] = freq.get(w, 0) + 1
    for term in chinese_terms:
        if term not in STOP_TERMS and len(term) >= 2:
            freq[term] = freq.get(term, 0) + 1

    if not must_have:
        fallback_skills = []
        if "项目经理" in text or "project manager" in text or "pjm" in text:
            fallback_skills.append("Project Management")
        if "产品" in text:
            fallback_skills.append("Product Management")
        if "ai" in text or "人工智能" in text:
            fallback_skills.append("Machine Learning")
        if "英语" in text or "english" in text:
            fallback_skills.append("English")
        if "数据" in text:
            fallback_skills.append("Business Analysis")
        must_have = fallback_skills

    top_terms = sorted(freq, key=freq.get, reverse=True)[:8]

    if role == "project_manager":
        must_have = sorted(
            set(must_have + ["Project Management", "Communication"]),
            key=lambda item: [
                "Project Management",
                "Communication",
                "Risk Management",
                "Resource Planning",
                "Python",
            ].index(item) if item in {
                "Project Management", "Communication", "Risk Management", "Resource Planning", "Python"
            } else 99
        )
        focus = ["planning", "delivery", "collaboration", "risk_control"]
    elif role == "commercial_ops":
        must_have = sorted(
            set(must_have + ["Commercial Operations", "Business Analysis", "English"]),
            key=lambda item: [
                "Commercial Operations",
                "Business Analysis",
                "Product Management",
                "English",
            ].index(item) if item in {
                "Commercial Operations", "Business Analysis", "Product Management", "English"
            } else 99
        )
        focus = ["product", "operations", "market", "global_ops"]
    elif role == "ai_product_ops":
        must_have = sorted(
            set(must_have + ["AI Product Operations", "Commercial Operations", "Product Management", "A/B Testing"]),
            key=lambda item: [
                "AI Product Operations",
                "Commercial Operations",
                "Product Management",
                "A/B Testing",
                "English",
            ].index(item) if item in {
                "AI Product Operations", "Commercial Operations", "Product Management", "A/B Testing", "English"
            } else 99
        )
        focus = ["product", "operations", "content_ops", "experiment"]
    elif role == "data_product_manager":
        must_have = sorted(
            set(must_have + ["Product Management", "Business Analysis", "Communication"]),
            key=lambda item: [
                "Product Management",
                "Business Analysis",
                "Communication",
                "Python",
                "SQL",
            ].index(item) if item in {
                "Product Management", "Business Analysis", "Communication", "Python", "SQL"
            } else 99
        )
        focus = ["product", "analysis", "collaboration", "delivery"]
    elif role == "quality_management":
        must_have = sorted(
            set(must_have + ["Quality Management", "Project Management", "Risk Management", "Communication", "English"]),
            key=lambda item: [
                "Quality Management",
                "Project Management",
                "Risk Management",
                "Communication",
                "English",
            ].index(item) if item in {
                "Quality Management", "Project Management", "Risk Management", "Communication", "English"
            } else 99
        )
        focus = ["quality_ops", "planning", "delivery", "risk_control"]
    elif role in {"ml_engineer", "ai_app_engineer"}:
        must_have = sorted(
            set(must_have + ["Machine Learning", "Python"]),
            key=lambda item: [
                "Machine Learning",
                "Python",
                "NLP",
                "Communication",
            ].index(item) if item in {
                "Machine Learning", "Python", "NLP", "Communication"
            } else 99
        )
        focus = [item for item in ["ml", "pipeline", "delivery", "collaboration"] if item in set(focus + ["ml", "pipeline"])]

    return {
        "role": role,
        "must_have_skills": must_have[:6],
        "focus_areas": focus[:4],
        "top_terms": top_terms,
    }
