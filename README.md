# AI Resume Tailoring Agent

根据岗位 JD 自动生成定制化简历，支持：

- 中文 / 英文简历生成
- 自动识别岗位方向
- 自动挑选最相关项目
- 导出 Markdown / PDF
- Streamlit 网页版

## 1. 安全说明

仓库已经默认忽略以下真实敏感文件：

- `.env`
- `outputs/`
- `inputs/jd.txt`
- `data/profile.json`
- `data/project_bank.json`

公开仓库中请只保留这些模板文件：

- `.env.example`
- `inputs/jd.example.txt`
- `data/profile.example.json`
- `data/project_bank.example.json`

如果你的 API key 曾经暴露过，请立刻去 OpenAI 后台重新生成新 key，并停用旧 key。

## 2. 本地准备

创建虚拟环境并安装依赖后，先复制模板文件：

```bash
cp .env.example .env
cp data/profile.example.json data/profile.json
cp data/project_bank.example.json data/project_bank.json
cp inputs/jd.example.txt inputs/jd.txt
```

然后把下面这些内容替换成你自己的：

- `.env` 里的 `OPENAI_API_KEY`
- `data/profile.json` 里的姓名、电话、邮箱、教育背景、工作经历、技能
- `data/project_bank.json` 里的项目经历
- `inputs/jd.txt` 里的岗位描述

## 3. 命令行运行

生成中文简历：

```bash
venv/bin/python src/main.py
```

程序会：

- 读取 `inputs/jd.txt`
- 识别岗位类型
- 选择最相关项目
- 生成 `outputs/tailored_resume.md`
- 生成 `outputs/tailored_resume.pdf`
- 自动复制 PDF 到 `~/Downloads`

## 4. 网页运行

启动 Streamlit：

```bash
venv/bin/streamlit run app.py
```

网页里可以直接填写：

- 岗位信息 / JD
- 个人信息
- 教育背景
- 工作经历
- 项目经历
- 技能与总结

适合给别人直接使用，不必改本地 JSON。

## 5. 上传到 GitHub

在确认敏感文件不会被提交后，再执行：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

提交前建议检查：

```bash
git status
```

不要把以下文件提交上去：

- `.env`
- `data/profile.json`
- `data/project_bank.json`
- `inputs/jd.txt`
- `outputs/`

## 6. 项目结构

```text
app.py                  # Streamlit 网页入口
src/main.py             # 主流程 / PDF 导出 / CLI 入口
src/matcher.py          # 岗位识别
src/jd_parser.py        # JD 结构化解析
src/scorer.py           # 项目打分与筛选
src/generator.py        # Prompt / API 调用 / 文本后处理
src/quality_checker.py  # 生成质量检查
data/                   # 候选人资料与项目库
inputs/                 # JD 输入
outputs/                # 生成结果
```

## 7. 给别人使用的建议

如果你准备把这个项目公开给别人用，建议：

- 保留 `.example` 模板
- 在 README 里告诉用户复制模板再填写
- 不公开任何真实个人资料
- 不公开任何真实 JD 输出结果
- 不共享你的 API key

