def _project_text(project):
    description_parts = []
    description_parts.extend(project.get("cn_bullets", []))
    description_parts.extend(project.get("en_bullets", []))
    return (
        project.get("name", "") +
        project.get("cn_title", "") +
        project.get("en_title", "") +
        " ".join(description_parts) +
        " ".join(project.get("role_tags", []))
    ).lower()


PROJECT_MANAGER_SIGNAL_TERMS = [
    "system", "platform", "workflow", "process", "delivery", "planning",
    "coordination", "stakeholder", "business decision", "decision support",
    "系统", "平台", "流程", "规划", "推进", "实施", "协作", "沟通", "决策支持",
    "跨平台", "整合", "优化", "质量",
]

PRODUCT_FIT_BONUS = {
    "AI Resume Tailoring Agent": {
        "ai_pm": 3,
        "ai_product_ops": 3,
        "data_product_manager": 2,
    },
}


def infer_project_category(project):
    tags = set(project.get("role_tags", []))
    if {"data_engineer"} & tags:
        return "data_engineering"
    if {"ai_app_engineer", "ai_pm"} & tags:
        return "ai"
    if {"business_analyst", "data_product_manager"} & tags:
        return "product"
    if {"data_scientist", "ml_engineer"} & tags:
        return "ml"
    return "analysis"


ROLE_CATEGORY_PREFERENCE = {
    "ai_app_engineer": {"ai": 3, "data_engineering": 2, "ml": 1},
    "ai_product_ops": {"product": 4, "ai": 2, "analysis": 2},
    "ml_engineer": {"ml": 3, "ai": 1, "data_engineering": 1},
    "data_analyst": {"analysis": 3, "product": 1},
    "business_analyst": {"analysis": 3, "product": 2},
    "data_product_manager": {"product": 3, "analysis": 1, "ai": 1},
    "project_manager": {"product": 3, "analysis": 2, "ai": 1},
    "commercial_ops": {"product": 3, "analysis": 3, "ai": 1},
    "quality_management": {"analysis": 3, "product": 2, "data_engineering": 1},
}


def score_project_details(project, jd_info):
    text = _project_text(project)
    category = infer_project_category(project)
    skill_score = 0
    matched_skills = []
    focus_score = 0
    matched_focus = []
    term_score = 0
    matched_terms = []
    category_bonus = 0

    for skill in jd_info["must_have_skills"]:
        if skill.lower() in text:
            skill_score += 3
            matched_skills.append(skill)

    for focus in jd_info["focus_areas"]:
        if focus in text:
            focus_score += 2
            matched_focus.append(focus)

    for term in jd_info["top_terms"]:
        if term in text:
            term_score += 1
            matched_terms.append(term)

    role = jd_info.get("role", "")
    tags = project.get("role_tags", [])
    if role and role in tags:
        category_bonus = 2
    category_bonus += ROLE_CATEGORY_PREFERENCE.get(role, {}).get(category, 0)
    category_bonus += PRODUCT_FIT_BONUS.get(project.get("name", ""), {}).get(role, 0)

    management_bonus = 0
    if role == "project_manager":
        if category in {"product", "analysis", "ai"}:
            management_bonus += 2
        elif category == "data_engineering":
            management_bonus += 1
        for term in PROJECT_MANAGER_SIGNAL_TERMS:
            if term in text:
                management_bonus += 1
        management_bonus = min(management_bonus, 5)
        category_bonus += management_bonus

    total = skill_score + focus_score + term_score + category_bonus
    reason_parts = []
    if matched_skills:
        reason_parts.append("Strong skill match: " + ", ".join(matched_skills[:3]))
    if matched_focus:
        reason_parts.append("Focus match: " + ", ".join(matched_focus[:2]))
    if category_bonus:
        reason_parts.append(f"Role-tag bonus for {role}")
    if PRODUCT_FIT_BONUS.get(project.get("name", ""), {}).get(role, 0):
        reason_parts.append("Strong product-fit bonus")
    if management_bonus:
        reason_parts.append("Project-management signal bonus")
    if matched_terms and not reason_parts:
        reason_parts.append("Term overlap: " + ", ".join(matched_terms[:3]))
    if not reason_parts:
        reason_parts.append("Weak direct match, kept only by broad term overlap")

    return {
        "project": project,
        "total": total,
        "skill_score": skill_score,
        "focus_score": focus_score,
        "term_score": term_score,
        "category_bonus": category_bonus,
        "matched_skills": matched_skills,
        "matched_focus": matched_focus,
        "matched_terms": matched_terms,
        "category": category,
        "reason": "; ".join(reason_parts),
    }


def score_project(project, jd_info):
    details = score_project_details(project, jd_info)
    return details["total"]


def pick_diverse_projects_by_role(scored_projects, role="", max_projects=3):
    selected = []
    used_names = set()
    used_categories = set()
    role_preferences = ROLE_CATEGORY_PREFERENCE.get(role, {})

    # Keep the strongest 2 matches first.
    for item in scored_projects:
        project = item["project"]
        name = project.get("name", "")
        if name in used_names:
            continue
        selected.append(project)
        used_names.add(name)
        used_categories.add(item["category"])
        if len(selected) >= min(2, max_projects):
            break

    # Prefer a distinct category, but do not sacrifice too much relevance.
    remaining = [item for item in scored_projects if item["project"].get("name", "") not in used_names]
    remaining.sort(
        key=lambda item: (
            item["total"],
            role_preferences.get(item["category"], 0),
            item["category_bonus"],
            item["skill_score"],
            item["focus_score"],
        ),
        reverse=True,
    )

    for item in remaining:
        project = item["project"]
        name = project.get("name", "")
        category = item["category"]
        if category in used_categories:
            continue
        selected.append(project)
        used_names.add(name)
        used_categories.add(category)
        if len(selected) >= max_projects:
            return selected

    for item in remaining:
        project = item["project"]
        name = project.get("name", "")
        if name in used_names:
            continue
        selected.append(project)
        used_names.add(name)
        if len(selected) >= max_projects:
            break

    return selected


def score_bullet_text(bullet: str, jd_info: dict) -> dict:
    text = bullet.lower()
    skill_score = 0
    focus_score = 0
    term_score = 0

    for skill in jd_info.get("must_have_skills", []):
        if skill.lower() in text:
            skill_score += 3

    for focus in jd_info.get("focus_areas", []):
        if focus in text:
            focus_score += 2

    for term in jd_info.get("top_terms", []):
        if term in text:
            term_score += 1

    return {
        "text": bullet,
        "total": skill_score + focus_score + term_score,
        "skill_score": skill_score,
        "focus_score": focus_score,
        "term_score": term_score,
    }


def trim_project_bullets(project: dict, jd_info: dict, max_bullets: int = 3) -> dict:
    trimmed = dict(project)

    cn_scored = [score_bullet_text(b, jd_info) for b in project.get("cn_bullets", [])]
    en_scored = [score_bullet_text(b, jd_info) for b in project.get("en_bullets", [])]

    cn_scored.sort(key=lambda item: item["total"], reverse=True)
    en_scored.sort(key=lambda item: item["total"], reverse=True)

    trimmed["cn_bullets"] = [item["text"] for item in cn_scored[:max_bullets]]
    trimmed["en_bullets"] = [item["text"] for item in en_scored[:max_bullets]]
    trimmed["_bullet_debug"] = {
        "cn": cn_scored,
        "en": en_scored,
    }
    return trimmed


def prepare_projects_for_generation(projects: list[dict], jd_info: dict, max_bullets: int = 3) -> list[dict]:
    return [trim_project_bullets(project, jd_info, max_bullets=max_bullets) for project in projects]
