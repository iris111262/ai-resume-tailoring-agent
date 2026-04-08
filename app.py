import json
import os
import re
import sys

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from main import load_json_prefer_example, run_resume_pipeline


def bullets_from_text(text: str) -> list[str]:
    return [line.strip().lstrip("-").strip() for line in text.splitlines() if line.strip()]


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\\\/:*?"<>|]', "_", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("._") or "resume"


def build_profile_from_form(
    name: str,
    phone: str,
    email: str,
    edu1_school: str,
    edu1_degree: str,
    edu1_dates: str,
    edu1_coursework: str,
    edu2_school: str,
    edu2_degree: str,
    edu2_dates: str,
    edu2_coursework: str,
    work_company: str,
    work_title: str,
    work_dates: str,
    work_bullets: str,
    skills_text: str,
    summary_text: str,
) -> dict:
    education = []
    if edu1_school.strip():
        education.append({
            "school": edu1_school.strip(),
            "degree": edu1_degree.strip(),
            "dates": edu1_dates.strip(),
            "coursework": edu1_coursework.strip(),
        })
    if edu2_school.strip():
        education.append({
            "school": edu2_school.strip(),
            "degree": edu2_degree.strip(),
            "dates": edu2_dates.strip(),
            "coursework": edu2_coursework.strip(),
        })

    skills_cn = {}
    for line in skills_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "：" in line:
            key, value = line.split("：", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            key, value = f"技能{len(skills_cn) + 1}", line
        skills_cn[key.strip()] = value.strip()

    return {
        "name_cn": name.strip(),
        "name_en": name.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "education_cn": education,
        "education_en": education,
        "work_experience_cn": {
            "company": work_company.strip(),
            "title": work_title.strip(),
            "dates": work_dates.strip(),
            "bullets": bullets_from_text(work_bullets),
        },
        "work_experience_en": {
            "company": work_company.strip(),
            "title": work_title.strip(),
            "dates": work_dates.strip(),
            "bullets": bullets_from_text(work_bullets),
        },
        "skills_cn": skills_cn,
        "skills_en": skills_cn,
        "summary_cn": summary_text.strip(),
        "summary_en": summary_text.strip(),
    }


def build_projects_from_form(project_inputs: list[dict]) -> list[dict]:
    projects = []
    for idx, item in enumerate(project_inputs, start=1):
        title = item["title"].strip()
        bullets = bullets_from_text(item["bullets"])
        if not title:
            continue
        projects.append({
            "name": title,
            "role_tags": item.get("role_tags", []),
            "priority": 5,
            "cn_title": title,
            "en_title": title,
            "cn_bullets": bullets,
            "en_bullets": bullets,
        })
    return projects


def render_card(title: str, subtitle: str = ""):
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="AI Resume Tailoring", page_icon="📄", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 233, 214, 0.8), transparent 28%),
            radial-gradient(circle at top right, rgba(219, 236, 255, 0.85), transparent 25%),
            linear-gradient(180deg, #fcfaf7 0%, #f4f1eb 100%);
    }
    .block-container {
        max-width: 1240px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        color: #222436;
        letter-spacing: -0.02em;
    }
    .hero {
        padding: 1.6rem 1.8rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,245,235,0.88));
        border: 1px solid rgba(193, 160, 123, 0.25);
        border-radius: 24px;
        box-shadow: 0 18px 40px rgba(52, 42, 28, 0.08);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 3.2rem;
        line-height: 1;
    }
    .hero p {
        margin: 0.65rem 0 0 0;
        color: #5b6274;
        font-size: 1.02rem;
    }
    .section-card {
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(170, 177, 197, 0.22);
        box-shadow: 0 10px 25px rgba(43, 46, 61, 0.05);
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1d2740;
        margin-bottom: 0.15rem;
    }
    .section-card p {
        margin: 0;
        color: #647089;
        font-size: 0.95rem;
    }
    .result-chip {
        display: inline-block;
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        background: #eef6ff;
        color: #1952a8;
        font-weight: 600;
        border: 1px solid rgba(30, 98, 185, 0.15);
    }
    div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.96);
        border-radius: 16px;
    }
    div[data-testid="stExpander"] {
        border-radius: 18px;
        border: 1px solid rgba(170, 177, 197, 0.2);
        background: rgba(255,255,255,0.78);
        overflow: hidden;
    }
    div.stButton > button {
        border-radius: 14px;
        border: none;
        background: linear-gradient(135deg, #ff7a59, #ff4f6d);
        color: white;
        font-weight: 700;
        padding: 0.7rem 1.15rem;
        box-shadow: 0 12px 24px rgba(255, 79, 109, 0.25);
    }
    div[data-testid="stDownloadButton"] > button {
        border-radius: 14px;
        font-weight: 700;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f7efe6 0%, #f0f4fb 100%);
        border-right: 1px solid rgba(182, 168, 152, 0.35);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

default_profile = load_json_prefer_example(os.path.join(PROJECT_ROOT, "data", "profile.json"))
default_projects = load_json_prefer_example(os.path.join(PROJECT_ROOT, "data", "project_bank.json"))

st.markdown(
    """
    <div class="hero">
        <h1>AI Resume Tailoring</h1>
        <p>Paste a job description, fill in candidate details, and generate a polished role-specific resume in minutes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Settings")
    lang = st.selectbox("Language", ["中文", "English"])
    language_code = "CN" if lang == "中文" else "EN"
    st.caption("Choose a language for the generated resume output.")

render_card("岗位信息 / Job Description", "岗位名称和岗位内容是最高优先级，系统会围绕 JD 来筛选经历和项目。")
jd_text = st.text_area(
    "Paste the JD here",
    height=260,
    placeholder="把岗位描述粘贴到这里 / Paste job description here...",
)

render_card("个人信息 / Personal Info", "填写候选人的基本信息，生成时会优先使用这里的内容。")
col1, col2, col3 = st.columns(3)
with col1:
    name = st.text_input("姓名 / Name", value=default_profile.get("name_cn", ""))
with col2:
    phone = st.text_input("电话 / Phone", value=default_profile.get("phone", ""))
with col3:
    email = st.text_input("邮箱 / Email", value=default_profile.get("email", ""))

render_card("教育背景 / Education", "支持两段教育经历，按时间倒序填写效果更好。")
edu1 = default_profile.get("education_cn", [{}])[0] if default_profile.get("education_cn") else {}
edu2 = default_profile.get("education_cn", [{}, {}])[1] if len(default_profile.get("education_cn", [])) > 1 else {}
edu_col1, edu_col2 = st.columns(2)
with edu_col1:
    edu1_school = st.text_input("学校 1", value=edu1.get("school", ""))
    edu1_degree = st.text_input("学位 1", value=edu1.get("degree", ""))
    edu1_dates = st.text_input("时间 1", value=edu1.get("dates", ""))
    edu1_coursework = st.text_area("课程 1", value=edu1.get("coursework", ""), height=100)
with edu_col2:
    edu2_school = st.text_input("学校 2", value=edu2.get("school", ""))
    edu2_degree = st.text_input("学位 2", value=edu2.get("degree", ""))
    edu2_dates = st.text_input("时间 2", value=edu2.get("dates", ""))
    edu2_coursework = st.text_area("课程 2", value=edu2.get("coursework", ""), height=100)

render_card("工作经历 / Work Experience", "每行一条 bullet，系统会根据 JD 自动压缩或突出最相关内容。")
default_work = default_profile.get("work_experience_cn", {})
work_col1, work_col2, work_col3 = st.columns(3)
with work_col1:
    work_company = st.text_input("公司", value=default_work.get("company", ""))
with work_col2:
    work_title = st.text_input("职位", value=default_work.get("title", ""))
with work_col3:
    work_dates = st.text_input("时间", value=default_work.get("dates", ""))
work_bullets = st.text_area(
    "工作 bullet points（每行一条）",
    value="\n".join(default_work.get("bullets", [])),
    height=140,
)

render_card("项目经历 / Projects", "默认带入你的项目库。给别人用时，他们可以在这里替换成自己的项目经历。")
project_inputs = []
project_count = max(len(default_projects), 8)
for idx in range(project_count):
    default_project = default_projects[idx] if idx < len(default_projects) else {}
    with st.expander(f"项目 {idx + 1}", expanded=(idx == 0)):
        title = st.text_input(
            f"项目名称 {idx + 1}",
            value=default_project.get("cn_title", default_project.get("name", "")),
            key=f"project_title_{idx}",
        )
        bullets = st.text_area(
            f"项目 bullet points {idx + 1}（每行一条）",
            value="\n".join(default_project.get("cn_bullets", [])),
            height=130,
            key=f"project_bullets_{idx}",
        )
        role_tags_text = st.text_input(
            f"项目角色标签 {idx + 1}（逗号分隔，可留空）",
            value=",".join(default_project.get("role_tags", [])),
            key=f"project_tags_{idx}",
        )
        role_tags = [x.strip() for x in role_tags_text.split(",") if x.strip()]
        project_inputs.append({
            "title": title,
            "bullets": bullets,
            "role_tags": role_tags,
        })

render_card("技能与总结 / Skills and Summary", "技能可以按“分类：内容”填写，自我评价会作为补充语气来源。")
skills_text = st.text_area(
    "技能（每行一条，可写成：分类：内容）",
    value="\n".join(f"{k}：{v}" for k, v in default_profile.get("skills_cn", {}).items()),
    height=160,
)
summary_text = st.text_area(
    "自我评价 / Summary",
    value=default_profile.get("summary_cn", ""),
    height=120,
)

if "result" not in st.session_state:
    st.session_state.result = None

action_col1, action_col2 = st.columns([1, 3])
with action_col1:
    generate_clicked = st.button("Generate Resume", type="primary")

if generate_clicked:
    if not jd_text.strip():
        st.warning("请先输入岗位描述。")
    else:
        with st.spinner("正在生成简历，请稍等..."):
            try:
                profile_override = build_profile_from_form(
                    name=name,
                    phone=phone,
                    email=email,
                    edu1_school=edu1_school,
                    edu1_degree=edu1_degree,
                    edu1_dates=edu1_dates,
                    edu1_coursework=edu1_coursework,
                    edu2_school=edu2_school,
                    edu2_degree=edu2_degree,
                    edu2_dates=edu2_dates,
                    edu2_coursework=edu2_coursework,
                    work_company=work_company,
                    work_title=work_title,
                    work_dates=work_dates,
                    work_bullets=work_bullets,
                    skills_text=skills_text,
                    summary_text=summary_text,
                )
                projects_override = build_projects_from_form(project_inputs)
                result = run_resume_pipeline(
                    jd_text=jd_text,
                    language=language_code,
                    export_download=False,
                    show_logs=False,
                    profile_override=profile_override,
                    projects_override=projects_override,
                )
                st.session_state.result = result
                st.success("简历生成成功。")
            except Exception as e:
                st.error(f"生成失败：{e}")

result = st.session_state.result

if result:
    render_card("生成结果 / Output", "系统会优先使用 JD 标题作为岗位名称，并只保留和 JD 相关的经历与项目。")
    top_col1, top_col2 = st.columns([1.2, 2.8])
    with top_col1:
        st.markdown("**Detected Role**")
        st.markdown(
            f"<div class='result-chip'>{result.get('job_title') or result.get('role')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("**Selected Projects**")
        for p in result.get("selected_projects", []):
            st.write(f"- {p}")

    with top_col2:
        st.markdown("**Resume Preview**")
        st.text_area(
            "Generated Resume",
            value=result.get("resume_text", ""),
            height=520,
            label_visibility="collapsed",
        )

    md_path = result.get("md_path")
    pdf_path = result.get("pdf_path")
    job_title = sanitize_filename(result.get("job_title") or result.get("role") or "resume")

    col1, col2 = st.columns(2)

    with col1:
        if md_path and os.path.exists(md_path):
            with open(md_path, "rb") as f:
                st.download_button(
                    "Download Markdown",
                    data=f.read(),
                    file_name=f"{job_title}.md",
                    mime="text/markdown",
                )

    with col2:
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download PDF",
                    data=f.read(),
                    file_name=f"{job_title}.pdf",
                    mime="application/pdf",
                )
