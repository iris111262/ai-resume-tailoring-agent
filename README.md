# 🧠 AI Resume Tailoring Agent

An AI-powered tool that automatically generates **job-specific resumes** based on job descriptions (JD), helping candidates tailor resumes efficiently for different roles.

根据岗位 JD 自动生成定制化简历，提升简历匹配度与求职效率。

---

## 🚀 Key Features | 核心功能

* 🎯 **JD-driven resume generation**
  自动解析岗位 JD，识别岗位方向（如 Data Analyst / AI PM）

* 🧩 **Smart project selection**
  基于关键词匹配 + 打分机制，自动筛选最相关项目

* 🌍 **Bilingual support**
  支持 **中英文简历生成**

* 📄 **Multi-format export**
  导出 **Markdown + PDF**

* 🌐 **Web interface (Streamlit)**
  提供可视化网页操作界面（无需改代码）

---

## 🏗️ System Architecture | 系统结构

```
JD Input → JD Parser → Project Scorer → Resume Generator → Output (MD/PDF)
```

### Core Modules

* `jd_parser.py` → JD结构化解析
* `scorer.py` → 项目打分与排序
* `generator.py` → LLM生成简历
* `quality_checker.py` → 输出质量控制

---

## 🛠️ Tech Stack

* Python
* OpenAI API (LLM)
* Streamlit
* PDFKit
* Prompt Engineering

---

## 📊 Example Workflow

1. 输入岗位 JD
2. 自动识别岗位类型
3. 筛选最相关项目
4. 生成定制化简历
5. 导出 PDF

---

## 💡 Why This Project Matters

传统写简历的问题：

* ❌ 通用模板，缺乏针对性
* ❌ 手动修改效率低
* ❌ 难以匹配不同岗位

本项目解决：

* ✅ 自动化简历定制
* ✅ 提高岗位匹配度
* ✅ 提升通过筛选概率

---

## 🔐 1. 安全说明

仓库已经默认忽略以下真实敏感文件：

* `.env`
* `outputs/`
* `inputs/jd.txt`
* `data/profile.json`
* `data/project_bank.json`

公开仓库中请只保留这些模板文件：

* `.env.example`
* `inputs/jd.example.txt`
* `data/profile.example.json`
* `data/project_bank.example.json`

⚠️ 如果你的 API key 曾经暴露，请立即重新生成并停用旧 key。

---

## ⚙️ 2. 本地准备

创建虚拟环境并安装依赖后：

```bash
cp .env.example .env
cp data/profile.example.json data/profile.json
cp data/project_bank.example.json data/project_bank.json
cp inputs/jd.example.txt inputs/jd.txt
```

然后填写：

* `.env` → OpenAI API Key
* `profile.json` → 个人信息
* `project_bank.json` → 项目经历
* `jd.txt` → 岗位 JD

---

## 🖥️ 3. 命令行运行

```bash
python src/main.py
```

程序会：

* 读取 JD
* 识别岗位类型
* 筛选项目
* 生成 Markdown + PDF
* 自动复制 PDF 到下载目录

---

## 🌐 4. 网页运行（推荐）

```bash
streamlit run app.py
```

支持直接填写：

* JD
* 个人信息
* 教育 / 工作经历
* 项目经历
* 技能

👉 适合非技术用户使用

---

## 📦 5. 上传到 GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

提交前检查：

```bash
git status
```

🚫 不要上传：

* `.env`
* `data/profile.json`
* `data/project_bank.json`
* `inputs/jd.txt`
* `outputs/`

---

## 📁 6. 项目结构

```
app.py                  # Streamlit UI
src/main.py             # 主流程 / CLI入口
src/jd_parser.py        # JD解析
src/scorer.py           # 项目评分
src/generator.py        # LLM生成
src/quality_checker.py  # 质量检查
data/                   # 模板数据
inputs/                 # JD输入
outputs/                # 输出结果
```

---

## 🚀 7. Future Improvements

* JD匹配度评分（Match Score）
* 批量生成简历
* 自动投递（Auto Apply）
* Prompt优化

---

## 📌 Notes

* 不要上传真实个人信息
* 不要暴露 API key
* 使用 `.example` 模板

---

## ⭐ Highlights（写给 Recruiter）

* Built an AI-powered resume generation system using LLM
* Designed a JD parsing + project scoring pipeline
* Automated resume customization workflow
* Reduced manual resume editing effort significantly

---
