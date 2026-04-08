import json
import os
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from matcher import extract_keywords_from_jd, classify_role, get_project_match_debug, extract_jd_title
from generator import generate_resume
from jd_parser import parse_jd_info
from quality_checker import check_resume_quality
from scorer import score_project_details, pick_diverse_projects_by_role, prepare_projects_for_generation

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTION_HEADERS = {
    "教育背景", "工作经历", "工作经验", "项目经历", "项目经验", "技能", "技能专长", "核心技能", "自我评价",
    "Education", "Work Experience", "Projects", "Skills", "Summary",
}


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_json_prefer_example(path: str):
    if os.path.exists(path):
        return load_json(path)
    root, ext = os.path.splitext(path)
    example_path = f"{root}.example{ext}"
    if os.path.exists(example_path):
        return load_json(example_path)
    raise FileNotFoundError(f"Missing required JSON file: {path}")


def load_text_prefer_example(path: str):
    if os.path.exists(path):
        return load_text(path)
    root, ext = os.path.splitext(path)
    example_path = f"{root}.example{ext}"
    if os.path.exists(example_path):
        return load_text(example_path)
    raise FileNotFoundError(f"Missing required text file: {path}")


def save_output(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


ROLE_DISPLAY_NAMES = {
    "CN": {
        "data_engineer": "数据开发工程师",
        "ai_pm": "AI产品经理",
        "ai_product_ops": "AI工具产品运营",
        "commercial_ops": "商业化运营",
        "quality_management": "质量管理",
        "project_manager": "项目经理",
        "ai_app_engineer": "AI应用工程师",
        "data_analyst": "数据分析师",
        "business_analyst": "商业分析师",
        "data_scientist": "数据科学家",
        "ml_engineer": "算法工程师",
        "data_product_manager": "数据产品经理",
    },
    "EN": {
        "data_engineer": "Data_Engineer",
        "ai_pm": "AI_Product_Manager",
        "ai_product_ops": "AI_Tool_Product_Ops",
        "commercial_ops": "Commercial_Ops",
        "quality_management": "Quality_Management",
        "project_manager": "Project_Manager",
        "ai_app_engineer": "AI_Application_Engineer",
        "data_analyst": "Data_Analyst",
        "business_analyst": "Business_Analyst",
        "data_scientist": "Data_Scientist",
        "ml_engineer": "ML_Engineer",
        "data_product_manager": "Data_Product_Manager",
    },
}


def build_export_filename(file_path: str, profile: dict, role: str, language: str, job_title: str = "") -> str:
    ext = os.path.splitext(file_path)[1]
    role_name = job_title.strip() or ROLE_DISPLAY_NAMES.get(language, {}).get(role, role or "resume")
    if language == "CN":
        person_name = profile.get("name_cn", "简历").strip() or "简历"
        return f"{person_name}_{role_name}_简历{ext}"
    person_name = profile.get("name_en", "Resume").strip().replace(" ", "_") or "Resume"
    return f"{person_name}_{role_name}_Resume{ext}"


def export_to_downloads(file_path: str, filename: str | None = None) -> str | None:
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(downloads_dir):
        return None

    filename = filename or os.path.basename(file_path)
    destination = os.path.join(downloads_dir, filename)
    shutil.copy2(file_path, destination)
    return destination


def save_lines(path: str, lines: list[str]):
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def score_bar(score: int, unit: str = "█", max_width: int = 12) -> str:
    width = min(max(score, 0), max_width)
    return unit * width if width > 0 else "-"


def build_decision_visual_report(
    role: str,
    jd_info: dict,
    scored_projects: list[dict],
    selected_projects: list[dict],
    quality_findings: list[str] | None = None,
) -> list[str]:
    lines = [
        "# Resume Decision Report",
        "",
        "## JD Structured Info",
        f"- Role: `{role}`",
        f"- Must-have skills: {', '.join(jd_info.get('must_have_skills', [])) or 'none'}",
        f"- Focus areas: {', '.join(jd_info.get('focus_areas', [])) or 'none'}",
        f"- Top terms: {', '.join(jd_info.get('top_terms', [])) or 'none'}",
        "",
        "## Project Scoring Overview",
        "| Project | Total | Visual | Skill | Focus | Term | Bonus | Category |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]

    selected_names = {project.get("name", "") for project in selected_projects}
    for item in scored_projects:
        name = item["project"]["name"]
        marker = "Selected" if name in selected_names else ""
        lines.append(
            f"| {name} {marker} | {item['total']} | {score_bar(item['total'])} | "
            f"{item['skill_score']} | {item['focus_score']} | {item['term_score']} | "
            f"{item['category_bonus']} | {item['category']} |"
        )

    lines.extend([
        "",
        "## Why Selected",
    ])
    for item in scored_projects:
        name = item["project"]["name"]
        if name not in selected_names:
            continue
        lines.append(f"### {name}")
        lines.append(f"- Reason: {item['reason']}")
        lines.append(
            f"- Score breakdown: skill={item['skill_score']}, focus={item['focus_score']}, "
            f"term={item['term_score']}, bonus={item['category_bonus']}"
        )
        bullet_debug = item["project"].get("_bullet_debug", {}).get("cn", [])
        if bullet_debug:
            lines.append("- Bullet trimming:")
            for bullet in bullet_debug[:3]:
                lines.append(
                    f"  - [{bullet['total']}] {bullet['text']}"
                )
        lines.append("")

    lines.append("## Final Selected Projects")
    for project in selected_projects:
        lines.append(f"- {project['name']}")

    if quality_findings is not None:
        lines.extend([
            "",
            "## Resume Quality Check",
        ])
        for item in quality_findings:
            lines.append(f"- {item}")

    return lines


def get_pdf_font_name(language: str) -> str:
    if language == "CN":
        font_name = "STSong-Light"
        try:
            pdfmetrics.getFont(font_name)
        except KeyError:
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        return font_name
    return "Helvetica"


def strip_markdown_for_pdf(line: str) -> str:
    return line.replace("**", "").strip()


def get_profile_photo_path() -> str:
    return os.path.join(PROJECT_ROOT, "image.png")


def normalize_contact_text(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("：", ":")
        .replace(" ", "")
    )


def strip_leading_contact_block(lines: list[str], language: str = "CN", profile: dict | None = None) -> list[str]:
    body_lines = lines[:]
    patterns = (
        ["个人信息", "姓名:", "电话:", "手机:", "邮箱:"]
        if language == "CN"
        else ["personal information", "name:", "phone:", "mobile:", "email:"]
    )
    exact_lines = set()
    if profile:
        if language == "CN":
            exact_lines.update({
                normalize_contact_text(profile.get("name_cn", "").strip()),
                normalize_contact_text(f"电话:{profile.get('phone', '')}".strip()),
                normalize_contact_text(f"手机:{profile.get('phone', '')}".strip()),
                normalize_contact_text(f"邮箱:{profile.get('email', '')}".strip()),
            })
        else:
            exact_lines.update({
                normalize_contact_text(profile.get("name_en", "").strip()),
                normalize_contact_text(f"Phone:{profile.get('phone', '')}".strip()),
                normalize_contact_text(f"Mobile:{profile.get('phone', '')}".strip()),
                normalize_contact_text(f"Email:{profile.get('email', '')}".strip()),
            })

    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    while body_lines:
        stripped = body_lines[0].strip()
        normalized = normalize_contact_text(stripped)
        if (
            normalized in exact_lines
            or any(normalized == p or normalized.startswith(p) for p in patterns)
        ):
            body_lines.pop(0)
            continue
        break

    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    return body_lines


def save_pdf(path: str, content: str, profile: dict | None = None, language: str = "CN"):
    try:
        # 使用reportlab生成支持中文的PDF
        doc = SimpleDocTemplate(
            path,
            pagesize=letter,
            leftMargin=28,
            rightMargin=28,
            topMargin=28,
            bottomMargin=28,
        )
        styles = getSampleStyleSheet()
        font_name = get_pdf_font_name(language)

        # 创建自定义样式
        name_style = ParagraphStyle(
            'ResumeName',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=28,
            leading=32,
            leftIndent=20,
            firstLineIndent=0,
            spaceAfter=6,
            alignment=0,
        )

        contact_style = ParagraphStyle(
            'ResumeContact',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11.5,
            leading=15,
            leftIndent=20,
            spaceAfter=3,
        )

        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            leading=18,
            leftIndent=20,
            textColor="#111111",
            spaceAfter=8,
        )

        entry_title_style = ParagraphStyle(
            'EntryTitle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12.4,
            leading=16,
            leftIndent=20,
            textColor="#111111",
            spaceAfter=4,
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11.5,
            leading=15,
            leftIndent=20,
            textColor="#111111",
            spaceAfter=5,
        )

        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11.5,
            leading=15,
            leftIndent=34,
            bulletIndent=22,
            textColor="#111111",
            spaceAfter=4,
        )

        meta_style = ParagraphStyle(
            'ProjectMeta',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11.5,
            leading=15,
            textColor="#444444",
            leftIndent=20,
            spaceAfter=4,
        )

        skills_style = ParagraphStyle(
            'SkillsLine',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11.5,
            leading=15,
            leftIndent=20,
            textColor="#111111",
            spaceAfter=4,
        )

        skills_bullet_style = ParagraphStyle(
            'SkillsBullet',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10.8,
            leading=14,
            leftIndent=26,
            bulletIndent=16,
            textColor="#111111",
            spaceAfter=3,
        )

        story = []

        lines = content.split('\n')
        body_lines = lines[:]

        if profile:
            if language == "CN":
                display_name = profile.get("name_cn", "")
                contact_lines = [
                    f"电话：{profile.get('phone', '')}",
                    f"邮箱：{profile.get('email', '')}",
                ]
            else:
                display_name = profile.get("name_en", "")
                contact_lines = [
                    f"Phone: {profile.get('phone', '')}",
                    f"Email: {profile.get('email', '')}",
                ]

            left_block = [
                Paragraph(display_name, name_style),
                Spacer(1, 2),
                Paragraph(contact_lines[0], contact_style),
                Paragraph(contact_lines[1], contact_style),
            ]

            photo_cell = Spacer(1, 1)
            photo_path = get_profile_photo_path()
            if language == "CN" and os.path.exists(photo_path):
                photo = Image(photo_path, width=1.0 * inch, height=1.25 * inch)
                photo.hAlign = "RIGHT"
                photo_cell = photo

            header = Table(
                [[left_block, photo_cell]],
                colWidths=[5.7 * inch, 1.3 * inch],
            )
            header.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (1, 0), (1, 0), -12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            header.hAlign = "LEFT"
            story.append(header)
            story.append(Spacer(1, 4))

            body_lines = strip_leading_contact_block(body_lines, language=language, profile=profile)

        current_section = []
        in_bullet_list = False

        current_section_style = normal_style
        active_section = ""

        for line in body_lines:
            line = strip_markdown_for_pdf(line)
            if not line:
                if current_section:
                    # 添加段落
                    para_text = '<br/>'.join(current_section)
                    if in_bullet_list:
                        active_bullet_style = skills_bullet_style if active_section in {"技能", "技能专长", "核心技能", "Skills"} else bullet_style
                        story.append(Paragraph(para_text, active_bullet_style))
                    else:
                        story.append(Paragraph(para_text, current_section_style))
                    story.append(Spacer(1, 6))
                    current_section = []
                    current_section_style = normal_style
                    in_bullet_list = False
                continue

            if line.startswith('- '):
                # 这是项目符号
                if not in_bullet_list:
                    in_bullet_list = True
                bullet_text = line[2:]  # 移除 "- "
                current_section.append(bullet_text)
            else:
                # 普通文本
                if in_bullet_list:
                    # 如果之前是项目符号列表，先处理它
                    if current_section:
                        para_text = '<br/>'.join(current_section)
                        active_bullet_style = skills_bullet_style if active_section in {"技能", "技能专长", "核心技能", "Skills"} else bullet_style
                        story.append(Paragraph(para_text, active_bullet_style))
                        story.append(Spacer(1, 6))
                    current_section = []
                    current_section_style = normal_style
                    in_bullet_list = False

                # 检查是否是标题（没有标点符号的短行）
                if line.startswith("项目类型：") or line.startswith("Project Type:"):
                    current_section.append(line)
                    para_text = '<br/>'.join(current_section)
                    story.append(Paragraph(para_text, meta_style))
                    story.append(Spacer(1, 4))
                    current_section = []
                elif line.startswith("核心课程：") or line.startswith("Relevant Coursework:"):
                    current_section.append(line)
                    para_text = '<br/>'.join(current_section)
                    story.append(Paragraph(para_text, meta_style))
                    story.append(Spacer(1, 2))
                    current_section = []
                    current_section_style = normal_style
                elif line in SECTION_HEADERS:
                    if current_section:
                        para_text = '<br/>'.join(current_section)
                        story.append(Paragraph(para_text, current_section_style))
                        story.append(Spacer(1, 6))
                        current_section = []
                        current_section_style = normal_style
                    story.append(Paragraph(f"<b>{line}</b>", section_style))
                    story.append(Spacer(1, 4))
                    active_section = line
                elif (
                    len(line) < 50
                    and "：" not in line
                    and ":" not in line
                    and not any(p in line for p in '.,;:!?')
                ):
                    current_section.append(f"<b>{line}</b>")
                    current_section_style = entry_title_style
                elif " | " in line:
                    current_section.append(line)
                    current_section_style = ParagraphStyle(
                        'WorkOrProjectLine',
                        parent=normal_style,
                        leftIndent=12,
                        leading=15,
                    )
                else:
                    current_section.append(line)
                    current_section_style = skills_style if active_section in {"技能", "技能专长", "核心技能", "Skills"} else normal_style

        # 处理最后的段落
        if current_section:
            para_text = '<br/>'.join(current_section)
            if in_bullet_list:
                active_bullet_style = skills_bullet_style if active_section in {"技能", "技能专长", "核心技能", "Skills"} else bullet_style
                story.append(Paragraph(para_text, active_bullet_style))
            else:
                story.append(Paragraph(para_text, normal_style))

        doc.build(story)
        print("PDF生成成功（支持中文，使用ReportLab）")

    except Exception as e:
        print(f"PDF生成失败: {e}")
        # 如果PDF生成失败，至少保存Markdown
        md_path = path.replace('.pdf', '.md')
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"已保存Markdown版本: {md_path}")


def ask_language_choice() -> str:
    print("请选择生成简历的语言 / Please choose resume language:")
    print("1. 中文")
    print("2. English")
    print("提示：建议一次只生成一种语言版本，更节省 API 成本。")
    choice = input("请输入 1 或 2 / Enter 1 or 2: ").strip()

    if choice == "1":
        return "CN"
    elif choice == "2":
        return "EN"
    else:
        print("输入无效，默认使用 English。")
        return "EN"


def is_cheap_mode_enabled() -> bool:
    value = os.getenv("RESUME_CHEAP_MODE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def ask_jd_input() -> str:
    """优先从文件读取JD文本；如果没有，再让用户手动输入。"""
    jd_file = "inputs/jd.txt"
    if os.path.exists(jd_file):
        jd_text = load_text(jd_file).strip()
        if jd_text:
            print(f"\n📄 已从 {jd_file} 读取岗位要求")
            return jd_text

    print("\n请输入职位描述 (JD) 文本 / Please paste job description text:")
    print("(直接回车跳过，将使用岗位类型手动选择 / Press Enter to skip, will use role selection)")
    print("-" * 50)

    lines = []
    while True:
        try:
            line = input()
            if not line and not lines:  # 第一次回车且没有内容
                return ""
            elif not line:  # 空行结束输入
                break
            lines.append(line)
        except EOFError:
            break

    return "\n".join(lines)


def ask_role_choice() -> str:
    """当没有JD文本时，让用户手动选择岗位类型"""
    print("\n请选择岗位类型 / Please choose role type:")
    print("1. 数据开发工程师 / Data Engineer")
    print("2. AI产品经理 / AI Product Manager")
    print("3. 商业化运营 / Commercial Ops")
    print("4. 质量管理 / Quality Management")
    print("5. 项目经理 / Project Manager")
    print("6. AI应用开发工程师 / AI Application Engineer")
    print("7. 数据分析师 / Data Analyst")
    print("8. 商业分析师 / Business Analyst")
    print("9. 数据科学家 / Data Scientist")
    print("10. 算法工程师 / ML Engineer")
    print("11. 数据产品经理 / Data Product Manager")

    choice = input("请输入 1-11 / Enter 1-11: ").strip()

    role_map = {
        "1": "data_engineer",
        "2": "ai_pm",
        "3": "commercial_ops",
        "4": "quality_management",
        "5": "project_manager",
        "6": "ai_app_engineer",
        "7": "data_analyst",
        "8": "business_analyst",
        "9": "data_scientist",
        "10": "ml_engineer",
        "11": "data_product_manager"
    }

    selected_role = role_map.get(choice)
    if not selected_role:
        print("输入无效，默认选择数据分析师 / Invalid input, defaulting to Data Analyst")
        selected_role = "data_analyst"

    return selected_role


def get_openai_client(show_logs: bool = True):
    client = None
    try:
        import os
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv(dotenv_path=".env")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            if show_logs:
                print("✅ OpenAI API 可用，将使用纯API生成模式")
                print("提示：如需更省 token，可在 .env 中设置 RESUME_CHEAP_MODE=true")
        else:
            raise RuntimeError("未检测到 OPENAI_API_KEY，当前项目已配置为纯API模式。")
    except ImportError:
        raise RuntimeError("未安装 OpenAI 依赖，当前项目已配置为纯API模式。")
    return client


def run_resume_pipeline(
    jd_text: str,
    language: str = "CN",
    export_download: bool = False,
    show_logs: bool = False,
    profile_override: dict | None = None,
    projects_override: list[dict] | None = None,
) -> dict:
    client = get_openai_client(show_logs=show_logs)

    profile = profile_override or load_json_prefer_example("data/profile.json")
    projects = projects_override or load_json_prefer_example("data/project_bank.json")
    rules = load_json("data/resume_rules.json")
    prompt_template = load_text("prompts/generate_resume.txt")
    cheap_mode = is_cheap_mode_enabled()
    if cheap_mode and show_logs:
        print("💸 已启用低成本模式：更少项目、更短JD、更低输出上限")

    jd_text = jd_text.strip()
    if not jd_text:
        raise ValueError("JD text is required.")

    if show_logs:
        print(f"\n📄 收到JD文本 ({len(jd_text)} 字符)")
    role = classify_role(jd_text)
    job_title = extract_jd_title(jd_text)
    if show_logs:
        print(f"🤖 自动识别岗位类型: {role}")

    if show_logs:
        print(f"DEBUG: Selected language code: {language}")

    jd_keywords = extract_keywords_from_jd(jd_text)
    if show_logs:
        print("\nMatched JD keywords:", jd_keywords)

    jd_info = parse_jd_info(jd_text, role=role)
    if show_logs:
        print("\nJD structured info:")
        print(jd_info)

    project_debug = get_project_match_debug(projects, role, jd_text=jd_text)
    debug_lines = [
        f"Role: {role}",
        f"Job title: {job_title or 'none'}",
        f"Matched JD keywords: {', '.join(j['keyword'] for j in extract_keywords_from_jd(jd_text)) or 'none'}",
        "",
        "Project match scores:",
    ]
    if show_logs:
        print("\nProject match scores:")
    for item in project_debug:
        matched_keywords = ", ".join(item["matched_keywords"]) if item["matched_keywords"] else "none"
        line = (
            f"- {item['name']}: total={item['total_score']} "
            f"(role={item['role_score']}, keyword={item['keyword_score']}, priority={item['priority_score']}) "
            f"| matched keywords: {matched_keywords}"
        )
        if show_logs:
            print(line)
        debug_lines.append(line)

    debug_file = "outputs/project_match_debug.txt"
    save_lines(debug_file, debug_lines)
    if show_logs:
        print(f"\n项目匹配明细已保存: {debug_file}")

    scored_projects = [score_project_details(project, jd_info) for project in projects]
    scored_projects.sort(key=lambda item: item["total"], reverse=True)

    scored_lines = [
        "Project selection debug:",
        f"Role: {role}",
        f"Job title: {job_title or 'none'}",
        f"Must-have skills: {', '.join(jd_info['must_have_skills']) or 'none'}",
        f"Focus areas: {', '.join(jd_info['focus_areas']) or 'none'}",
        "",
    ]
    if show_logs:
        print("\nProject selection details:")
    for item in scored_projects:
        line = (
            f"- {item['project']['name']}: total={item['total']} "
            f"(skill={item['skill_score']}, focus={item['focus_score']}, "
            f"term={item['term_score']}, category_bonus={item['category_bonus']}) "
            f"| reason={item['reason']}"
        )
        if show_logs:
            print(line)
        scored_lines.append(line)

    selected_projects = pick_diverse_projects_by_role(scored_projects, role=role, max_projects=3)
    scored_lines.append("")
    scored_lines.append("Selected projects:")
    for project in selected_projects:
        scored_lines.append(f"- {project['name']}")

    selected_projects = prepare_projects_for_generation(
        selected_projects,
        jd_info,
        max_bullets=rules.get("max_bullets_per_project", 3),
    )
    scored_lines.append("")
    scored_lines.append("Trimmed project bullets:")
    for project in selected_projects:
        scored_lines.append(f"- {project['name']}")
        for item in project.get("_bullet_debug", {}).get("cn", [])[: rules.get("max_bullets_per_project", 3)]:
            scored_lines.append(
                f"  CN bullet total={item['total']} "
                f"(skill={item['skill_score']}, focus={item['focus_score']}, term={item['term_score']}): "
                f"{item['text']}"
            )

    save_lines("outputs/project_selection_debug.txt", scored_lines)
    if show_logs:
        print("\n项目筛选明细已保存: outputs/project_selection_debug.txt")

    if show_logs:
        print("\nSelected projects:")
        for p in selected_projects:
            print("-", p["name"])

    resume_text = generate_resume(
        profile=profile,
        selected_projects=selected_projects,
        language=language,
        client=client,
        rules=rules,
        jd_text=jd_text,
        jd_info=jd_info,
        prompt_template=prompt_template,
        cheap_mode=cheap_mode,
    )
    resume_lines = strip_leading_contact_block(
        resume_text.splitlines(),
        language=language,
        profile=profile,
    )
    resume_text = "\n".join(resume_lines).strip() + "\n"

    output_file = "outputs/tailored_resume.md"
    ensure_parent_dir(output_file)
    save_output(output_file, resume_text)

    pdf_file = "outputs/tailored_resume.pdf"
    save_pdf(pdf_file, resume_text, profile=profile, language=language)

    export_pdf_name = build_export_filename(pdf_file, profile=profile, role=role, language=language, job_title=job_title)
    exported_pdf = export_to_downloads(pdf_file, filename=export_pdf_name) if export_download else None

    if show_logs:
        print(f"\n简历已生成: {output_file}")
        print(f"PDF版本: {pdf_file}")
        if exported_pdf:
            print(f"已自动复制PDF到下载文件夹: {exported_pdf}")
        print("\n===== GENERATED RESUME =====")
        print(resume_text)

    quality_findings = check_resume_quality(resume_text, jd_info)
    quality_lines = ["Resume Quality Check:"]
    quality_lines.extend([f"- {item}" for item in quality_findings])
    save_lines("outputs/resume_quality_check.txt", quality_lines)
    if show_logs:
        print("\nResume Quality Check:")
        for item in quality_findings:
            print(f"- {item}")

    decision_visual_lines = build_decision_visual_report(
        role=role,
        jd_info=jd_info,
        scored_projects=scored_projects,
        selected_projects=selected_projects,
        quality_findings=quality_findings,
    )
    save_lines("outputs/decision_report.md", decision_visual_lines)
    if show_logs:
        print("\n可视化决策报告已保存: outputs/decision_report.md")

    return {
        "resume_text": resume_text,
        "md_path": output_file,
        "pdf_path": pdf_file,
        "selected_projects": [p["name"] for p in selected_projects],
        "jd_info": jd_info,
        "role": role,
        "job_title": job_title,
        "quality_findings": quality_findings,
        "exported_pdf_path": exported_pdf,
        "debug_paths": {
            "project_match": debug_file,
            "project_selection": "outputs/project_selection_debug.txt",
            "quality_check": "outputs/resume_quality_check.txt",
            "decision_report": "outputs/decision_report.md",
        },
    }


def main():
    jd_text = ask_jd_input()
    if jd_text.strip():
        language = ask_language_choice()
        run_resume_pipeline(
            jd_text=jd_text,
            language=language,
            export_download=True,
            show_logs=True,
        )
        return

    print("\n📋 未提供JD文本，将进行手动岗位选择")
    role = ask_role_choice()
    print(f"👤 手动选择岗位类型: {role}")
    language = ask_language_choice()
    run_resume_pipeline(
        jd_text=f"岗位类型: {role}",
        language=language,
        export_download=True,
        show_logs=True,
    )


if __name__ == "__main__":
    main()
