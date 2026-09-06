# AI-Assisted Ad Landing Page Risk Review System

## English

### Overview

This project is a product prototype for ad downstream risk review. In digital advertising, a creative can look compliant, but after a user clicks it, the landing page may redirect to phishing forms, deceptive financial claims, forced downloads, sensitive content, or device-specific cloaking experiences.

The goal is not to build a generic web crawler. The goal is to design a reviewer-facing risk workflow that helps ad review, policy, risk operations, and AI teams detect downstream landing page risk with clear evidence and measurable quality metrics.

### Product Problem

Ad reviewers often need to inspect landing pages manually. This creates several product and operational problems:

- Risk can appear only after redirects, scrolling, clicks, form interactions, mobile rendering, ad referer access, or geo-specific delivery.
- Manual review is slow, inconsistent, and difficult to audit.
- Reviewers need evidence, not only a black-box risk score.
- Policy teams need structured signals to understand emerging abuse patterns.
- AI and model teams need labeled, evidence-backed examples to improve automated review.

### Target Users

- Ad reviewers: need faster evidence collection for approve, reject, or escalate decisions.
- Risk operations teams: need consistent downstream review workflows and measurable quality.
- Policy teams: need structured examples to validate and refine policy labels.
- AI and model teams: need high-quality signals and reviewer feedback for model improvement.
- Risk product managers: need metrics, thresholds, roadmap tradeoffs, and cross-functional execution plans.

### Product Goals

MVP goals:

- Reduce manual effort needed to inspect ad landing pages.
- Surface downstream risk signals with reviewer-friendly evidence.
- Provide an explainable baseline score before introducing more advanced AI automation.
- Preserve screenshots, redirect chains, forms, links, risk terms, and false-positive notes.
- Measure review quality with precision, recall, false positive rate, manual agreement, and risk discovery metrics.

North star goal:

- Build an AI-assisted downstream risk review platform that improves risky landing page discovery while maintaining reviewer trust and policy explainability.

### MVP Scope

The current MVP includes:

- URL submission workflow.
- Playwright-based landing page crawl.
- Extraction of page title, visible text, hidden text, links, forms, redirect chain, screenshots, download signals, password fields, and phone fields.
- Rule-based risk scoring with policy labels and evidence.
- Tiered policy lexicons with high, medium, and low confidence terms.
- Context snippets for matched risk terms.
- Basic negation filtering, for example "no crypto" is not treated as crypto promotion.
- Multi-signal combinations, such as financial terms plus earnings claims.
- False-positive notes for reviewer calibration.
- Optional LLM semantic review using structured evidence.
- Optional controlled browser automation for scrolling, CTA clicking, fake form filling, and screenshot trail generation.
- Optional multi-environment cloaking check across desktop, mobile, and ad-referer contexts.
- Evaluation metrics from labeled review data.
- FastAPI backend, Streamlit UI, and SQLite scan history.

### Product Workflow

```text
Landing page URL submitted
-> Browser-based page crawl
-> Redirect, DOM, text, form, link, screenshot, and download signal extraction
-> Rule-based risk scoring with evidence
-> Optional dynamic downstream exploration
-> Optional LLM semantic review with guardrails
-> Reviewer-facing risk summary, labels, confidence, and false-positive notes
-> Saved scan history and evaluation metrics
```

### Success Metrics

Primary product metrics:

- Review time per landing page.
- Risk discovery rate.
- False positive rate.
- Manual reviewer agreement rate.
- Evidence completeness rate.
- Escalation rate to policy team.

Model and system quality metrics:

- Precision.
- Recall.
- False positive rate.
- Average downstream exploration depth.
- Unsupported LLM label rejection rate.
- Scan success rate and timeout rate.

### Cross-Functional Execution

This project is designed as a cross-functional PM case:

- Policy team: define risk categories, enforcement labels, and reviewer escalation criteria.
- Review operations: validate evidence format, workflow fit, and false-positive handling.
- Engineering: build crawler, signal extraction, scoring service, scan storage, and UI.
- AI/model team: design semantic review prompts, structured outputs, and label guardrails.
- Data team: create labeled evaluation data and define quality metrics.
- Legal/privacy stakeholders: review automation boundaries, fake data usage, and data retention.

### Key Product Tradeoffs

- Rule-based baseline vs LLM-only automation: rules are more explainable and auditable; LLM is used as an assistive semantic layer.
- High recall vs false positives: the MVP surfaces evidence and confidence so reviewers can calibrate decisions.
- Automation depth vs safety: dynamic exploration uses fake data and stops around sensitive gates instead of blindly clicking everything.
- Fast MVP vs full geo cloaking: the system includes a geo cloaking framework, but real geo detection requires regional proxy infrastructure.
- Reviewer trust vs full automation: the first version supports human decision-making instead of replacing reviewers.

### Technical Implementation

The implementation supports the product workflow:

- `backend/app/main.py`: FastAPI API layer.
- `backend/app/scanner.py`: scan orchestration.
- `backend/app/crawler/browser.py`: Playwright crawl and screenshot capture.
- `backend/app/analyzer/rules.py`: evidence-backed risk scoring.
- `backend/app/automation/flow_runner.py`: controlled downstream user simulation.
- `backend/app/analyzer/cloaking.py`: environment mismatch and cloaking checks.
- `backend/app/llm/policy_reasoner.py`: optional LLM semantic review and guardrails.
- `ui/streamlit_app.py`: reviewer-facing UI.

### Setup

```bash
cd ad-landing-risk-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Optional LLM reasoning:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4o-mini"
```

Optional geo cloaking:

```bash
cp storage/geo_environments.example.json storage/geo_environments.json
# Edit storage/geo_environments.json with real regional proxy servers.
```

Without real proxies, geo cloaking is skipped because timezone and locale do not change IP geolocation.

### Run API

```bash
cd ad-landing-risk-analyzer
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

Example:

```bash
curl -X POST http://127.0.0.1:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","dynamic":false,"use_llm":false,"cloaking":false}'
```

### Run UI

```bash
cd ad-landing-risk-analyzer
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

### PM Case Study

See [docs/PM_CASE_STUDY.md](docs/PM_CASE_STUDY.md) for a bilingual PM-focused case study covering user needs, requirements, cross-functional execution, metrics, tradeoffs, and roadmap.

---

## 中文

### 项目概览

这个项目是一个广告后链路风险审核的产品原型。在广告审核场景中，广告素材本身可能看起来合规，但用户点击后进入的 landing page 可能存在钓鱼表单、虚假金融承诺、强制下载、敏感内容，或者基于设备和来源展示不同内容的 cloaking 行为。

这个项目的目标不是做一个普通网页爬虫，而是设计一个面向审核员的风险审核流程，帮助广告审核、政策、风控运营和 AI 团队用清晰证据和可量化指标识别落地页风险。

### 用户问题

广告审核员经常需要手动检查落地页，这会带来几个产品和运营问题：

- 风险内容可能只在跳转、滚动、点击、表单交互、移动端渲染、广告 referer 或特定地区访问时出现。
- 人工审核速度慢、一致性弱，也难以追溯。
- 审核员需要证据，而不只是一个黑盒风险分。
- 政策团队需要结构化信号来理解新型风险模式。
- AI 和模型团队需要带证据的标注样本来优化自动化审核能力。

### 目标用户

- 广告审核员：更快收集证据，用于通过、拒绝或升级审核。
- 风控运营团队：需要稳定的后链路审核流程和可衡量的质量指标。
- 政策团队：需要结构化案例来验证和优化政策标签。
- AI 和模型团队：需要高质量信号和人工反馈来改进模型。
- 风控产品经理：需要指标、阈值、路线图取舍和跨团队执行方案。

### 产品目标

MVP 目标：

- 降低人工检查广告落地页的成本。
- 用审核员可理解的证据展示后链路风险。
- 在引入更复杂 AI 自动化前，先建立可解释的 baseline 风险分。
- 保留截图、跳转链、表单、链接、风险词和误报提示。
- 用 precision、recall、false positive rate、manual agreement、risk discovery 等指标衡量审核质量。

北极星目标：

- 构建一个 AI 辅助的广告后链路风险审核平台，在提升风险发现率的同时，保持审核员信任和政策可解释性。

### MVP 范围

当前 MVP 包含：

- URL 提交流程。
- 基于 Playwright 的 landing page 抓取。
- 提取页面标题、可见文本、隐藏文本、链接、表单、跳转链、截图、下载信号、密码字段和手机号字段。
- 基于规则的风险评分、政策标签和证据展示。
- 高、中、低置信度的政策风险词库。
- 风险词上下文片段。
- 基础否定过滤，例如 "no crypto" 不会被当作 crypto 推广。
- 多信号组合识别，例如金融词汇加收益承诺。
- 用于审核校准的误报提示。
- 可选 LLM 语义复核，且基于结构化证据。
- 可选受控浏览器自动化，包括滚动、CTA 点击、fake form filling 和截图轨迹。
- 可选多环境 cloaking 检测，包括 desktop、mobile 和 ad-referer。
- 基于标注数据的评估指标。
- FastAPI 后端、Streamlit UI 和 SQLite 扫描历史。

### 产品流程

```text
提交 landing page URL
-> 浏览器抓取页面
-> 提取跳转、DOM、文本、表单、链接、截图和下载信号
-> 基于规则生成有证据的风险分
-> 可选动态后链路探索
-> 可选带 guardrail 的 LLM 语义复核
-> 输出面向审核员的风险总结、标签、置信度和误报提示
-> 保存扫描历史并计算评估指标
```

### 成功指标

核心产品指标：

- 单个 landing page 的审核耗时。
- 风险发现率。
- 误报率。
- 人工审核一致率。
- 证据完整率。
- 升级到政策团队的比例。

模型和系统质量指标：

- Precision。
- Recall。
- False positive rate。
- 平均后链路探索深度。
- LLM 无证据标签拒绝率。
- 扫描成功率和超时率。

### 跨团队执行

这个项目可以作为一个跨团队 PM case：

- 政策团队：定义风险类别、执行标签和审核升级标准。
- 审核运营：验证证据格式、工作流适配度和误报处理方式。
- 工程团队：建设 crawler、信号提取、评分服务、扫描存储和 UI。
- AI/模型团队：设计语义复核 prompt、结构化输出和标签 guardrail。
- 数据团队：构建标注评估数据并定义质量指标。
- 法务/隐私相关方：评估自动化边界、fake data 使用和数据保留策略。

### 关键产品取舍

- 规则 baseline vs 纯 LLM 自动化：规则更可解释、更容易审核；LLM 作为辅助语义层。
- 高召回 vs 误报：MVP 输出证据和置信度，让审核员可以校准判断。
- 自动化深度 vs 安全边界：动态探索使用 fake data，并在敏感 gate 前停止，而不是盲目点击所有内容。
- 快速 MVP vs 完整 geo cloaking：系统包含 geo cloaking 框架，但真实 geo 检测需要地区代理基础设施。
- 审核员信任 vs 全自动判罚：第一版支持人工决策，而不是替代审核员。

### 技术实现

工程实现服务于上述产品流程：

- `backend/app/main.py`：FastAPI API 层。
- `backend/app/scanner.py`：扫描流程编排。
- `backend/app/crawler/browser.py`：Playwright 抓取和截图。
- `backend/app/analyzer/rules.py`：基于证据的风险评分。
- `backend/app/automation/flow_runner.py`：受控后链路用户模拟。
- `backend/app/analyzer/cloaking.py`：环境差异和 cloaking 检测。
- `backend/app/llm/policy_reasoner.py`：可选 LLM 语义复核和 guardrail。
- `ui/streamlit_app.py`：面向审核员的 UI。

### 运行方式

```bash
cd ad-landing-risk-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

启动 API：

```bash
uvicorn backend.app.main:app --reload --port 8000
```

启动 UI：

```bash
streamlit run ui/streamlit_app.py
```

### PM Case Study

可以查看 [docs/PM_CASE_STUDY.md](docs/PM_CASE_STUDY.md)，里面是中英双语的 PM 向案例复盘，覆盖用户需求、产品需求、跨团队执行、指标、取舍和路线图。
