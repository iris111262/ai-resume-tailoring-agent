import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def score_work_bullet(bullet: str, jd_info: dict | None) -> int:
    if not jd_info:
        return 0

    text = bullet.lower()
    score = 0
    for skill in jd_info.get("must_have_skills", []):
        if skill.lower() in text:
            score += 3
    for focus in jd_info.get("focus_areas", []):
        if focus in text:
            score += 2
    for term in jd_info.get("top_terms", []):
        if term in text:
            score += 1

    # Keep transferable data/business experience visible even when the JD is very technical.
    transferable_terms = [
        "数据", "分析", "流程", "业务", "决策", "协作",
        "data", "analysis", "process", "business", "decision", "stakeholder",
        "report", "sql", "python", "dashboard",
    ]
    if any(term in text for term in transferable_terms):
        score += 1
    return score


def score_work_bullet_direct_match(bullet: str, jd_info: dict | None) -> int:
    if not jd_info:
        return 0

    text = bullet.lower()
    score = 0
    for skill in jd_info.get("must_have_skills", []):
        if skill.lower() in text:
            score += 3
    for focus in jd_info.get("focus_areas", []):
        if focus in text:
            score += 2
    for term in jd_info.get("top_terms", []):
        if term in text:
            score += 1
    return score


def build_compact_work_experience(work: dict, role: str = "", jd_info: dict | None = None) -> dict:
    bullets = work.get("bullets", [])
    if not bullets:
        return {}

    scored = [
        (
            idx,
            bullet,
            score_work_bullet(bullet, jd_info),
            score_work_bullet_direct_match(bullet, jd_info),
        )
        for idx, bullet in enumerate(bullets)
    ]
    scored.sort(key=lambda item: (-item[2], -item[3], item[0]))

    top_score = scored[0][2] if scored else 0
    top_direct_score = scored[0][3] if scored else 0
    avg_top_two = (
        sum(item[2] for item in scored[:2]) / min(len(scored), 2)
        if scored else 0
    )

    max_bullets = 3
    if role in {"ai_app_engineer", "ml_engineer", "data_engineer"}:
        max_bullets = 2
        if top_direct_score == 0:
            return {}
        if top_score <= 1:
            max_bullets = 1
        if avg_top_two < 1:
            return {}
    elif role in {"data_analyst", "business_analyst", "data_product_manager", "ai_pm"}:
        max_bullets = 3

    selected = scored[:max_bullets]
    selected.sort(key=lambda item: item[0])
    return {
        "company": work.get("company", ""),
        "title": work.get("title", ""),
        "dates": work.get("dates", ""),
        "bullets": [bullet for _, bullet, _, _ in selected],
    }


def trim_work_bullets(work: dict, role: str = "", jd_info: dict | None = None) -> list[str]:
    bullets = work.get("bullets", [])
    if not bullets:
        return []

    max_bullets = 3
    if role in {"ai_app_engineer", "ml_engineer", "data_engineer"}:
        max_bullets = 2
    elif role in {"data_analyst", "business_analyst", "data_product_manager", "ai_pm"}:
        max_bullets = 3

    scored = [
        (idx, bullet, score_work_bullet(bullet, jd_info))
        for idx, bullet in enumerate(bullets)
    ]
    scored.sort(key=lambda item: (-item[2], item[0]))
    selected = scored[:max_bullets]
    selected.sort(key=lambda item: item[0])
    return [bullet for _, bullet, _ in selected]


def build_resume_payload(profile, selected_projects, language="CN", project_limit=3, role="", jd_info=None):
    if language == "CN":
        education = profile.get("education_cn", [])
        work = profile.get("work_experience_cn", {})
        skills = profile.get("skills_cn", {})
        name = profile.get("name_cn", "")
    else:
        education = profile.get("education_en", [])
        work = profile.get("work_experience_en", {})
        skills = profile.get("skills_en", {})
        name = profile.get("name_en", "")

    compact_education = [
        {
            "school": item.get("school", ""),
            "degree": item.get("degree", ""),
            "dates": item.get("dates", ""),
            "coursework": item.get("coursework", ""),
        }
        for item in education
    ]

    compact_work = {
        **build_compact_work_experience(work, role=role, jd_info=jd_info),
    }

    compact_projects = []
    for project in selected_projects[:project_limit]:
        if language == "CN":
            compact_projects.append({
                "title": project.get("cn_title", project.get("name", "")),
                "bullets": project.get("cn_bullets", []),
            })
        else:
            compact_projects.append({
                "title": project.get("en_title", project.get("name", "")),
                "bullets": project.get("en_bullets", []),
            })

    return {
        "language": language,
        "candidate": {
            "name": name,
            "phone": profile.get("phone", ""),
            "email": profile.get("email", ""),
            "education": compact_education,
            "work_experience": compact_work,
            "skills": skills,
        },
        "projects": compact_projects,
    }


def build_rules_text(rules):
    if isinstance(rules, dict):
        rule_items = rules.get("rules", [])
        if rule_items:
            return "\n".join(f"- {rule}" for rule in rule_items)
        return json.dumps(rules, ensure_ascii=False, indent=2)
    if isinstance(rules, list):
        return "\n".join(f"- {rule}" for rule in rules)
    return str(rules)


def normalize_resume_markdown(text: str) -> str:
    normalized_lines = []
    skip_next_nonempty = False
    for raw_line in text.splitlines():
        line = raw_line.lstrip()
        while line.startswith("#"):
            line = line[1:].lstrip()
        stripped = line.strip()
        lower = stripped.lower()

        # Remove markdown-style horizontal separators that look noisy in export.
        if stripped and set(stripped) <= {"-", "_", "*"} and len(stripped) >= 3:
            continue

        if stripped in {"期望岗位", "求职意向", "Expected Role", "Target Role", "Career Objective"}:
            skip_next_nonempty = True
            continue

        if skip_next_nonempty:
            if not stripped:
                continue
            skip_next_nonempty = False
            continue

        if (
            stripped.startswith("期待在")
            or stripped.startswith("期待加入")
            or stripped.startswith("希望在")
            or stripped.startswith("希望加入")
            or stripped.startswith("期望在")
            or stripped.startswith("期望加入")
            or lower.startswith("i hope to")
            or lower.startswith("looking to")
            or lower.startswith("seeking to")
            or lower.startswith("eager to")
            or lower.startswith("excited to join")
            or lower.startswith("looking forward to joining")
        ):
            continue

        if stripped.startswith("- 负责"):
            stripped = "- 主导" + stripped[len("- 负责"):]
        elif stripped.startswith("负责"):
            stripped = "主导" + stripped[len("负责"):]
        elif stripped.startswith("- 协助"):
            stripped = "- 支持" + stripped[len("- 协助"):]
        elif stripped.startswith("协助"):
            stripped = "支持" + stripped[len("协助"):]

        # Preserve the user's real project ownership; do not relabel personal products
        # as course projects unless that metadata actually exists in the source profile.
        stripped = stripped.replace("AI简历定制生成系统（课程项目）", "AI简历定制生成系统")
        stripped = stripped.replace("AI Resume Tailoring Agent (Course Project)", "AI Resume Tailoring Agent")

        normalized_lines.append(stripped.rstrip())
    return "\n".join(normalized_lines).strip() + "\n"


def compact_text(text: str, max_chars: int = 2200) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[:max_chars].rstrip() + "..."


def build_role_guidance(role: str, language: str) -> str:
    guidance = {
        "quality_management": {
            "CN": "如果JD明确是质量方向，则优先强调过程监控、质量评审、风险识别、问题闭环、跨团队协调、预警机制和英语工作能力；但仍以原始JD表述为准。",
            "EN": "If the JD is clearly quality-focused, emphasize process monitoring, quality reviews, risk identification, issue closure, cross-functional coordination, warning mechanisms, and working English; still defer to the exact JD wording first.",
        },
        "ai_product_ops": {
            "CN": "如果JD明确是AI工具产品运营，则优先强调AIGC工具理解、创意内容运营、海外社媒趋势洞察、A/B测试、用户运营、UGC生态和推动功能迭代；但仍以原始JD表述为准。",
            "EN": "If the JD is clearly for AI tool product operations, emphasize AIGC tool understanding, creative content operations, overseas social media trend analysis, A/B testing, user operations, UGC ecosystem building, and product iteration; still defer to the exact JD wording first.",
        },
        "commercial_ops": {
            "CN": "如果JD明确是商业化运营，则优先强调商业化设计、用户行为分析、问卷反馈、数据驱动调优、跨团队协作和游戏或产品理解；但仍以原始JD表述为准。",
            "EN": "If the JD is clearly for commercial operations, emphasize monetization design, user behavior analysis, survey feedback, data-driven tuning, cross-functional collaboration, and product or game understanding; still defer to the exact JD wording first.",
        },
        "data_product_manager": {
            "CN": "如果JD明确是技术产品或数据产品方向，则优先强调产品规划、需求理解、技术与业务协同、数据驱动迭代、跨团队沟通和推动落地；但仍以原始JD表述为准。",
            "EN": "If the JD is clearly for a technical or data product role, emphasize product planning, requirement understanding, tech-business collaboration, data-driven iteration, cross-functional communication, and execution; still defer to the exact JD wording first.",
        },
        "project_manager": {
            "CN": "如果JD明确是项目经理，则优先强调项目规划、资源协调、风险管理、跨团队沟通、推进与交付；但仍以原始JD表述为准。",
            "EN": "If the JD is clearly for a project manager role, emphasize planning, coordination, risk management, stakeholder communication, execution, and delivery; still defer to the exact JD wording first.",
        },
        "ai_app_engineer": {
            "CN": "如果JD明确是AI应用工程方向，则强调系统实现、模型或LLM应用、流程自动化、数据管道与工程落地；但仍以原始JD表述为准。",
            "EN": "If the JD is clearly for an AI application engineering role, emphasize system implementation, model or LLM application, automation, pipelines, and engineering execution; still defer to the exact JD wording first.",
        },
    }
    default_text = {
        "CN": "优先突出与岗位直接相关的经验和可迁移能力。",
        "EN": "Prioritize directly relevant experience and transferable strengths.",
    }
    return guidance.get(role, {}).get(language, default_text[language])


def generate_resume_with_openai(
    client,
    profile,
    selected_projects,
    rules,
    jd_text,
    jd_info,
    language="CN",
    prompt_template="",
    cheap_mode=False,
):
    project_limit = 3
    jd_limit = 1400 if cheap_mode else 2200
    output_limit = 1100 if cheap_mode else 1400

    payload = build_resume_payload(
        profile,
        selected_projects,
        language,
        project_limit=project_limit,
        role=jd_info.get("role", ""),
        jd_info=jd_info,
    )
    rules_text = build_rules_text(rules)
    max_bullets_per_project = rules.get("max_bullets_per_project", 3) if isinstance(rules, dict) else 3

    if language == "CN":
        language_instruction = "Output the resume in professional Simplified Chinese. Section headers should also be in Chinese."
    else:
        language_instruction = "Output the resume in polished professional English. Section headers should also be in English."

    prompt = prompt_template.format(
        role=jd_info["role"],
        skills=", ".join(jd_info["must_have_skills"]),
        focus=", ".join(jd_info["focus_areas"]),
        role_guidance=build_role_guidance(jd_info["role"], language),
        language_instruction=language_instruction,
        rules_text=rules_text,
        jd_text=compact_text(jd_text, max_chars=jd_limit),
        payload_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    ).strip()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=output_limit,
    )
    return normalize_resume_markdown(response.output_text)

def format_project(project, language="CN"):
    if language == "CN":
        title = project.get("cn_title", project["name"])
        bullets = project.get("cn_bullets", [])
    else:
        title = project.get("en_title", project["name"])
        bullets = project.get("en_bullets", [])

    bullet_text = "\n".join([f"- {b}" for b in bullets])
    return f"{title}\n{bullet_text}"


def build_education_section(profile, language="CN"):
    items = profile["education_cn"] if language == "CN" else profile["education_en"]

    lines = []
    for edu in items:
        if language == "CN":
            lines.append(f"{edu['school']}")
            lines.append(f"{edu['degree']}")
            lines.append(f"{edu['dates']}")
            lines.append("核心课程：")
            lines.append(f"{edu['coursework']}")
            lines.append("")
        else:
            lines.append(f"{edu['school']}")
            lines.append(f"{edu['degree']}")
            lines.append(f"{edu['dates']}")
            lines.append("Relevant Coursework:")
            lines.append(f"{edu['coursework']}")
            lines.append("")

    return "\n".join(lines).strip()


def build_work_section(profile, language="CN"):
    work = profile["work_experience_cn"] if language == "CN" else profile["work_experience_en"]

    if language == "CN":
        lines = [
            f"{work['company']}",
            f"{work['title']}",
            f"{work['dates']}"
        ]
    else:
        lines = [
            f"{work['company']}",
            f"{work['title']}",
            f"{work['dates']}"
        ]

    lines.extend([f"- {b}" for b in work["bullets"]])
    return "\n".join(lines)


def build_skills_section(profile, language="CN"):
    skills = profile["skills_cn"] if language == "CN" else profile["skills_en"]

    lines = []
    for k, v in skills.items():
        lines.append(f"{k}")
        lines.append(f"{v}")
    return "\n".join(lines)


def generate_resume(
    profile,
    selected_projects,
    language="CN",
    client=None,
    rules=None,
    jd_text="",
    jd_info=None,
    prompt_template="",
    cheap_mode=False,
):
    if client is None:
        raise ValueError("OpenAI client is required in API-only mode.")
    if rules is None:
        raise ValueError("Resume rules are required in API-only mode.")
    if not jd_text.strip():
        raise ValueError("JD text is required in API-only mode.")
    if jd_info is None:
        raise ValueError("JD structured info is required in API-only mode.")
    if not prompt_template.strip():
        raise ValueError("Prompt template is required in API-only mode.")

    return generate_resume_with_openai(
        client=client,
        profile=profile,
        selected_projects=selected_projects,
        rules=rules,
        jd_text=jd_text,
        jd_info=jd_info,
        language=language,
        prompt_template=prompt_template,
        cheap_mode=cheap_mode,
    )


def generate_html_resume(profile, selected_projects, language="EN"):
    with open("templates/resume_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    photo_path = os.path.join(PROJECT_ROOT, "image.png")
    photo_url = f"file://{photo_path}"

    if language == "CN":
        name = profile["name_cn"]
        contact = f"电话: {profile['phone']} | 邮箱: {profile['email']}"
        photo = photo_url
        summary = profile["summary_cn"]
    else:
        name = profile["name_en"]
        contact = f"Phone: {profile['phone']} | Email: {profile['email']}"
        photo = photo_url
        summary = profile["summary_en"]

    education = build_education_section(profile, language).replace("\n", "<br>")
    work = build_work_section(profile, language).replace("\n", "<br>")
    skills = build_skills_section(profile, language).replace("\n", "<br>")

    project_html = ""
    for p in selected_projects:
        if language == "CN":
            title = p["cn_title"]
            bullets = p["cn_bullets"]
        else:
            title = p["en_title"]
            bullets = p["en_bullets"]
        project_html += f"<b>{title}</b><ul>"
        for b in bullets:
            project_html += f"<li>{b}</li>"
        project_html += "</ul>"

    html = template.replace("{{name}}", name)\
        .replace("{{contact}}", contact)\
        .replace("{{photo}}", photo)\
        .replace("{{education}}", education)\
        .replace("{{work}}", work)\
        .replace("{{projects}}", project_html)\
        .replace("{{skills}}", skills)\
        .replace("{{summary}}", summary)

    return html
