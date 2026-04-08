def normalize_jd_text(jd_text: str) -> str:
    return (
        jd_text.lower()
        .replace("a!", "ai")
        .replace("a1", "ai")
        .replace("大语言模型", "llm")
        .replace("机器学习算法", "machine learning algorithm")
    )


def extract_jd_title(jd_text: str) -> str:
    ignored_lines = {
        "职位描述", "职位要求", "岗位职责", "任职要求",
        "recruit", "share", "分享", "申请职位", "apply",
        "job description", "requirements", "responsibilities",
        "工作地点", "更新时间",
    }
    for raw_line in jd_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = line.replace("【", "").replace("】", "").strip()
        lower = normalized.lower()
        if lower in ignored_lines or normalized in ignored_lines:
            continue
        if lower.startswith("工作地点") or lower.startswith("location"):
            continue
        if all(ch.isupper() or not ch.isalpha() for ch in normalized) and len(normalized) <= 12:
            continue
        return normalized
    return ""


KEYWORD_GROUPS = {
    "tools": {
        "python": 4,
        "sql": 4,
        "tableau": 4,
        "excel": 2,
        "power bi": 4,
        "spark": 5,
        "pyspark": 5,
        "kafka": 5,
        "nlp": 4,
        "编码": 3,
        "etl": 4,
        "dashboard": 3,
    },
    "analysis": {
        "data analysis": 4,
        "business analysis": 4,
        "visualization": 3,
        "reporting": 3,
        "automation": 3,
        "ab testing": 4,
        "a/b testing": 4,
        "retention": 3,
        "funnel": 3,
        "user behavior": 3,
        "stakeholder": 2,
        "strategy": 2,
        "operations": 2,
    },
    "ai": {
        "llm": 5,
        "ai": 4,
        "agent": 5,
        "machine learning": 5,
        "algorithm": 5,
        "机器学习": 5,
        "算法": 5,
        "ai应用": 4,
        "ai应用系统": 4,
        "deep learning": 5,
        "model": 3,
        "prediction": 3,
        "risk": 2,
    },
    "product": {
        "product": 3,
        "product manager": 4,
        "商业化运营": 5,
        "商业运营产品": 5,
        "商业化设计": 4,
        "运营产品岗位": 4,
        "market": 2,
        "growth": 2,
        "conversion": 3,
        "experiment": 2,
    },
    "project": {
        "project manager": 5,
        "program manager": 4,
        "project management": 5,
        "pjm": 5,
        "pmp": 4,
        "项目经理": 5,
        "项目管理": 5,
        "风险管理": 3,
        "kpi": 2,
        "stakeholder": 2,
        "resource": 2,
        "planning": 2,
    },
    "quality": {
        "质量": 5,
        "质量管理": 5,
        "质量方向": 5,
        "质量阀": 5,
        "评审": 3,
        "风险问题": 3,
        "闭环": 4,
        "质量改进": 4,
        "预警机制": 3,
        "风险评估": 3,
        "纠正措施": 3,
        "市场质量": 4,
    },
}


def extract_keywords_from_jd(jd_text: str) -> list[dict]:
    jd_lower = normalize_jd_text(jd_text)
    matched = []

    for group_name, keywords in KEYWORD_GROUPS.items():
        for keyword, weight in keywords.items():
            if keyword in jd_lower:
                matched.append({
                    "keyword": keyword,
                    "group": group_name,
                    "weight": weight,
                })

    return matched


def _project_search_text(project: dict) -> str:
    parts = [
        project.get("name", ""),
        project.get("cn_title", ""),
        project.get("en_title", ""),
        " ".join(project.get("cn_bullets", [])),
        " ".join(project.get("en_bullets", [])),
        " ".join(project.get("role_tags", [])),
    ]
    return " ".join(parts).lower()


def classify_role(jd_text: str) -> str:
    jd = normalize_jd_text(jd_text)
    title = normalize_jd_text(extract_jd_title(jd_text))

    # Hard-priority rule: if the title already names the role clearly, trust the title first.
    if "ai工具产品运营" in title or "aigc工具产品运营" in title:
        return "ai_product_ops"
    elif (
        "国际业务管理培训生" in title
        or "商用方向" in title
        or "国际业务" in title
        or "海外业务" in title
        or "management trainee" in title
        or "mt" in title and ("business" in title or "commercial" in title)
    ):
        return "commercial_ops"
    elif "商业化运营" in title or "商业运营产品" in title or "商业化设计" in title or "游戏商业化" in title:
        return "commercial_ops"
    elif "质量方向" in title or "质量管理" in title or "市场质量" in title:
        return "quality_management"
    elif "项目经理" in title or "pjm" in title or "project manager" in title or "program manager" in title:
        return "project_manager"
    elif "技术产品" in title or "技术产品经理" in title:
        return "data_product_manager"
    elif "产品经理培训生" in title or "产品经理" in title or "product manager" in title:
        if "ai" in title or "asp" in title or "star program" in title:
            return "ai_pm"
        return "data_product_manager"
    elif (
        "算法工程师" in title
        or "algorithm" in title
        or "machine learning" in title
        or "机器学习" in title
        or "机器学习算法" in title
    ):
        return "ml_engineer"
    elif "ai应用开发" in title or "ai engineer" in title or "agent" in title:
        return "ai_app_engineer"

    if "数据开发" in jd or "data engineer" in jd or "spark" in jd or "etl" in jd or "kafka" in jd:
        return "data_engineer"
    elif "ai产品经理" in jd or ("product manager" in jd and "ai" in jd):
        return "ai_pm"
    elif "ai工具产品运营" in jd or "aigc工具产品运营" in jd:
        return "ai_product_ops"
    elif (
        "国际业务管理培训生" in jd
        or "商用方向" in jd
        or "国际业务" in jd
        or "海外业务" in jd
        or "海外市场" in jd
        or "国际化业务" in jd
        or "management trainee" in jd and ("business" in jd or "commercial" in jd)
    ):
        return "commercial_ops"
    elif "商业化运营" in jd or "商业运营产品" in jd or "商业化设计" in jd or "游戏商业化" in jd:
        return "commercial_ops"
    elif (
        "质量方向" in jd
        or "质量管理" in jd
        or "市场质量" in jd
        or "质量阀" in jd
        or "质量改进" in jd
    ):
        return "quality_management"
    elif "项目经理" in jd or "pjm" in jd or "project manager" in jd or "program manager" in jd or "项目管理" in jd:
        return "project_manager"
    elif "技术产品" in jd or "技术产品经理" in jd:
        return "data_product_manager"
    elif (
        "算法工程师" in jd
        or "algorithm" in jd
        or "machine learning" in jd
        or "机器学习" in jd
        or "deep learning" in jd
        or "大语言模型" in jd
        or "llm" in jd
        or "编码和算法基础" in jd
        or "机器学习算法" in jd
    ):
        return "ml_engineer"
    elif "ai应用开发" in jd or "ai应用系统" in jd or "ai engineer" in jd or "llm" in jd or "agent" in jd:
        return "ai_app_engineer"
    elif "商业分析" in jd or "business analyst" in jd or "strategy" in jd:
        return "business_analyst"
    elif "数据科学家" in jd or "data scientist" in jd:
        return "data_scientist"
    elif "数据产品经理" in jd or ("product manager" in jd and "data" in jd):
        return "data_product_manager"
    else:
        return "data_analyst"


def score_project(project: dict, role: str, jd_keywords: list[dict] | None = None) -> int:
    score = 0

    role_tags = project.get("role_tags", [])
    priority = project.get("priority", 1)

    if role in role_tags:
        score += 10

    project_text = _project_search_text(project)
    for keyword_info in jd_keywords or []:
        keyword = keyword_info["keyword"]
        weight = keyword_info["weight"]
        if keyword in project_text:
            score += weight

    score += priority
    return score


def explain_project_score(project: dict, role: str, jd_keywords: list[dict] | None = None) -> dict:
    role_tags = project.get("role_tags", [])
    priority = project.get("priority", 1)
    project_text = _project_search_text(project)

    matched_keywords = []
    keyword_score = 0
    for keyword_info in jd_keywords or []:
        keyword = keyword_info["keyword"]
        weight = keyword_info["weight"]
        if keyword in project_text:
            matched_keywords.append(keyword)
            keyword_score += weight

    role_score = 10 if role in role_tags else 0
    total_score = role_score + keyword_score + priority

    return {
        "name": project.get("name", ""),
        "total_score": total_score,
        "role_score": role_score,
        "priority_score": priority,
        "keyword_score": keyword_score,
        "matched_keywords": matched_keywords,
    }


def rank_projects(projects: list[dict], role: str, jd_text: str = "") -> list[dict]:
    jd_keywords = extract_keywords_from_jd(jd_text)
    scored = [(score_project(p, role, jd_keywords), p) for p in projects]
    scored.sort(key=lambda x: x[0], reverse=True)

    ranked = []
    selected_names = set()

    for score, project in scored:
        name = project["name"]
        if name in selected_names:
            continue

        ranked.append(project)
        selected_names.add(name)

    return ranked


def get_project_match_debug(projects: list[dict], role: str, jd_text: str = "") -> list[dict]:
    jd_keywords = extract_keywords_from_jd(jd_text)
    explanations = [explain_project_score(project, role, jd_keywords) for project in projects]
    explanations.sort(key=lambda item: item["total_score"], reverse=True)
    return explanations


def build_final_project_list(projects: list[dict], role: str, jd_text: str = "", top_k: int = 3) -> list[dict]:
    ranked = rank_projects(projects, role, jd_text=jd_text)

    resume_agent = None
    others = []

    for p in ranked:
        if p["name"] == "AI Resume Tailoring Agent":
            resume_agent = p
        else:
            others.append(p)

    if role in ["ai_pm", "ai_app_engineer", "data_product_manager", "project_manager", "commercial_ops", "ai_product_ops", "quality_management"]:
        final_projects = []
        if resume_agent:
            final_projects.append(resume_agent)
        final_projects.extend(others[: max(0, top_k - len(final_projects))])
        return final_projects[:top_k]

    return ranked[:top_k]
