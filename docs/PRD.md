# PRD: AI-Powered Ad Landing Page Downstream Risk Analysis System

## English Version

### 1. Background

In international advertising review, risk is not limited to the ad creative itself. A compliant-looking ad may redirect users to a risky landing page after click. Downstream pages can expose users to phishing, forced downloads, deceptive financial claims, adult or sensitive content, hidden text, misleading redirects, or environment-based cloaking.

Traditional manual review is not enough for these cases because downstream risk may only appear after redirects, scrolling, clicking, form interaction, device-specific rendering, ad referer access, or geo-specific delivery.

This project proposes an AI-powered downstream landing page risk analysis system that combines browser automation, rule-based signal extraction, LLM semantic review, screenshot vision, cloaking detection, evidence generation, and evaluation metrics.

### 2. Problem Statement

Ad downstream review has several core challenges:

- Risk can be hidden after user interaction, redirects, or environment-specific rendering.
- Rule-only systems are brittle and can create false positives from weak keyword matches.
- LLM-only systems need evidence guardrails to avoid unsupported policy labels.
- Reviewers need clear evidence, not just a black-box risk score.
- Product and model teams need measurable metrics to evaluate improvement.

The goal is not to build a simple URL crawler. The goal is to build a downstream risk intelligence tool that supports ad review, risk strategy, and AI model improvement.

### 3. Target Users

- Ad reviewers: review evidence and make approve or reject decisions.
- Risk strategy product managers: analyze risk patterns, tune policies, and define thresholds.
- Model and AI teams: use structured risk signals and reviewer feedback to improve policy understanding.
- Policy teams: validate labels and refine enforcement guidelines.

### 4. Product Goals

MVP goals:

- Automatically crawl a submitted landing page URL.
- Extract title, visible text, hidden text, links, forms, redirects, download signals, and screenshots.
- Produce explainable risk score, risk level, policy labels, confidence, and evidence.
- Simulate limited downstream user flow with Playwright.
- Use LLM semantic reasoning to understand page intent and reduce false positives.
- Provide evaluation metrics for measuring system quality.

North star goal:

Build a scalable AI-assisted review system that improves downstream risk discovery while reducing manual review effort and false positives.

### 5. Risk Scope

In scope:

- Phishing and credential collection
- Adult or sensitive content
- Deceptive financial or crypto claims
- Forced download or suspicious download CTA
- Hidden text or cloaking-like content hiding
- Misleading redirect chains
- User data collection through forms
- Age gate, login wall, and cookie consent detection
- Device, User-Agent, and referer-based environment mismatch
- Geo cloaking framework with real regional proxies

Out of scope:

- Copyright or media ownership verification
- Malware binary reverse engineering
- Payment transaction monitoring
- Real geo cloaking without regional proxy infrastructure
- User identity verification

### 6. Product Workflow

```text
Input landing page URL
→ Playwright browser crawl
→ DOM, text, form, link, redirect, and screenshot extraction
→ Rule-based signal scoring
→ Dynamic user-flow simulation
→ Screenshot vision and LLM semantic review
→ LLM label guardrail and hybrid score fusion
→ Policy labels, evidence, confidence, and false-positive notes
→ Evaluation metrics dashboard
```

### 7. Core Capabilities

#### 7.1 Static Risk Scan

The system opens the URL with Playwright and extracts:

- Page title
- Visible text
- Hidden text
- Links
- Redirect chain
- Forms and input fields
- Password and phone fields
- Download CTA
- Risk terms and context snippets
- Screenshot

The rule layer provides a stable and explainable baseline score.

#### 7.2 Dynamic User Simulation

The system simulates a controlled user journey:

- Scroll the page
- Detect consent prompts
- Rank clickable actions by risk priority
- Click high-priority CTAs when safe
- Fill fake data into visible forms
- Save each step URL and screenshot
- Stop on age gates or repeated page states

The action policy prioritizes risky downstream paths such as download, claim, sign up, register, subscribe, or payment-related CTAs, while avoiding unsafe actions such as entering age-restricted content.

#### 7.3 LLM Semantic Review

Rules are strong at extracting stable signals, but weak at understanding semantic intent. The LLM layer is used for:

- Page intent classification
- Policy label suggestion
- Semantic false-positive analysis
- Reviewer-friendly summary
- Screenshot visual observation

The LLM receives structured evidence instead of raw unbounded webpage data:

```json
{
  "url": "...",
  "title": "...",
  "visible_text_excerpt": "...",
  "forms": [],
  "redirect_chain": [],
  "risk_term_evidence": {},
  "automation_steps": [],
  "rule_findings": []
}
```

The model returns structured output:

```json
{
  "page_intent": "adult_content",
  "policy_labels": ["Adult / Sexual Content"],
  "llm_risk_score": 75,
  "confidence": 0.9,
  "reviewer_summary": "...",
  "false_positive_assessment": [],
  "supporting_evidence": [],
  "visual_observations": []
}
```

#### 7.4 LLM Guardrails

To avoid hallucinated policy labels, the system applies label guardrails:

- The LLM can suggest labels.
- Final accepted labels must be supported by rule evidence or automation signals.
- Unsupported LLM labels are rejected and shown in false-positive notes.

Example:

```text
LLM suggested "Payment Collection", but no payment evidence was found.
Result: rejected_policy_labels = ["Payment Collection"]
```

This keeps the LLM useful for semantic reasoning while preserving evidence-grounded enforcement.

#### 7.5 Screenshot Vision

Some risk content may appear in images, modals, canvas, or visual banners. When LLM reasoning is enabled, the system sends the landing page screenshot as image input.

This helps detect:

- Visual warning text
- Age gate UI
- Image-only claims
- Button text not captured by DOM
- Screenshot-visible sensitive content

#### 7.6 Cloaking and Environment Mismatch Detection

The system scans the same URL across multiple environments:

- Desktop Chrome
- Mobile iPhone
- Ad-click referer

It compares:

- Final URL
- Risk score
- Text similarity
- Download CTA mismatch
- Password or form mismatch
- Screenshots

The system also includes a geo cloaking framework. Real geo detection requires regional proxies because locale and timezone do not change IP geolocation.

Example:

```text
US desktop → normal page
Indonesia mobile → APK download page
Result: high geo cloaking risk
```

### 8. Scoring Logic

The system uses a hybrid decision framework:

```text
Rule score = deterministic signal score
LLM score = semantic risk judgment
Final score = 0.6 * rule score + 0.4 * LLM score
```

If LLM confidence is low, the LLM weight is reduced.

Risk levels:

- Low: 0-39
- Medium: 40-69
- High: 70-100

The system also outputs confidence and false-positive notes to support reviewer judgment.

### 9. Evaluation Metrics

The product includes a labeled CSV evaluation workflow.

Core metrics:

- Precision: among pages predicted risky, how many are truly risky.
- Recall: among truly risky pages, how many were detected.
- False positive rate: benign pages incorrectly flagged as risky.
- Manual review agreement rate: overlap between system labels and reviewer labels.
- Risk discovery rate: percentage of scans where downstream automation finds extra risk signals.
- Average downstream depth: average number of downstream steps explored.
- Rejected LLM label rate: how often guardrails reject unsupported LLM labels.

These metrics help product and model teams evaluate whether system changes improve real review quality.

### 10. MVP Implementation

Current stack:

- Python
- Playwright
- BeautifulSoup
- FastAPI
- Streamlit
- SQLite
- OpenAI Responses API with Structured Outputs

Current repo structure:

```text
ad-landing-risk-analyzer/
  backend/
    app/
      crawler/
      analyzer/
      automation/
      llm/
      evaluation/
      db/
  ui/
  storage/
  docs/
```

### 11. Roadmap

V1: MVP Risk Analyzer

- URL scan
- Rule-based score
- Evidence extraction
- Streamlit UI
- SQLite history

V2: Automated Downstream Exploration

- Controlled browser automation
- CTA ranking
- Form filling
- Screenshot trail
- Age gate, login wall, and cookie prompt detection

V3: AI Review Layer

- LLM semantic review
- Screenshot vision
- Label guardrails
- Hybrid score fusion
- False-positive analysis

V4: Advanced Risk Governance

- Multi-path exploration
- OCR over all downstream screenshots
- Real geo cloaking with proxy pool
- Reviewer feedback loop
- Clustering similar risky landing pages
- Policy threshold tuning dashboard

### 12. Business Value

This system can support business integrity teams by:

- Increasing downstream risk discovery
- Reducing manual review workload
- Improving consistency of policy decisions
- Producing reusable evidence for reviewer decisions
- Helping strategy teams quantify policy impact
- Creating structured risk samples for AI model improvement

This is not just a technical demo. It is an AI product prototype for ad review risk governance, covering business problem definition, risk signal abstraction, model application, evaluation design, and product iteration planning.

---

## 中文版

### 1. 项目背景

在国际化广告审核场景中，风险不只存在于广告素材本身。一个看起来合规的广告，在用户点击后可能跳转到高风险落地页。后链路页面可能包含钓鱼、强制下载、虚假金融承诺、成人或敏感内容、隐藏文本、误导性跳转，或基于设备、来源、地域展示不同内容的 cloaking 行为。

传统人工审核很难稳定覆盖这些风险，因为风险内容可能只在跳转、滚动、点击、表单交互、移动端渲染、广告 referer 或特定地区访问时出现。

本项目提出一个 AI 驱动的广告落地页后链路风险识别系统，结合浏览器自动化、规则信号提取、LLM 语义复核、截图视觉理解、cloaking 检测、审核证据链和评估指标体系。

### 2. 核心问题

广告后链路审核存在几个核心挑战：

- 风险可能隐藏在跳转、点击、表单交互或环境差异之后。
- 纯规则系统容易因为弱关键词命中产生误报。
- 纯 LLM 系统如果没有证据约束，可能生成没有依据的政策标签。
- 审核员需要可解释证据，而不是黑盒分数。
- 产品和模型团队需要量化指标来评估系统是否真的变好。

本项目目标不是构建一个简单 URL 爬虫，而是构建一个支持广告审核、风控策略分析和 AI 模型迭代的后链路风险分析工具。

### 3. 目标用户

- 广告审核员：查看风险证据并做出通过或拒绝决策。
- 风控策略产品经理：分析风险模式、调整策略、定义阈值。
- 模型和 AI 团队：使用结构化风险信号和人工反馈优化模型能力。
- 政策团队：验证政策标签并完善执行标准。

### 4. 产品目标

MVP 目标：

- 自动抓取用户提交的 landing page URL。
- 提取标题、可见文本、隐藏文本、链接、表单、跳转链、下载信号和截图。
- 输出可解释的风险分数、风险等级、政策标签、置信度和证据。
- 使用 Playwright 模拟有限的用户后链路路径。
- 使用 LLM 进行语义判断，理解页面意图并降低误报。
- 提供评估指标来衡量系统效果。

北极星目标：

构建一个可扩展的 AI 辅助审核系统，提升广告后链路风险发现率，同时降低人工审核成本和误报率。

### 5. 风险范围

项目范围内：

- 钓鱼和账号凭证收集
- 成人或敏感内容
- 虚假金融或加密货币承诺
- 强制下载或可疑下载按钮
- 隐藏文本或类似 cloaking 的内容隐藏
- 误导性跳转链
- 通过表单收集用户信息
- 年龄门槛、登录墙、cookie consent 检测
- 设备、User-Agent、referer 维度的环境差异
- 基于真实地区代理的 geo cloaking 扩展框架

项目范围外：

- 版权或媒体所有权验证
- 恶意文件二进制逆向分析
- 支付交易监控
- 没有地区代理基础设施时的真实 geo cloaking
- 用户身份验证

版权盗版、恶意文件逆向、支付交易监控等属于其他治理域，当前 MVP 不作为核心范围。

### 6. 产品流程

```text
输入 landing page URL
→ Playwright 浏览器抓取
→ DOM、文本、表单、链接、跳转链和截图提取
→ 规则信号评分
→ 动态用户路径模拟
→ 截图视觉理解和 LLM 语义复核
→ LLM 标签防幻觉约束和混合分数融合
→ 政策标签、证据、置信度和误报分析
→ 评估指标看板
```

### 7. 核心能力

#### 7.1 静态风险扫描

系统使用 Playwright 打开 URL，并提取：

- 页面标题
- 可见文本
- 隐藏文本
- 页面链接
- 跳转链
- 表单和输入字段
- 密码字段和手机号字段
- 下载按钮
- 风险词和上下文片段
- 页面截图

规则层输出稳定、可解释的 baseline 风险分数。

#### 7.2 动态用户模拟

系统模拟受控用户路径：

- 滚动页面
- 检测 consent 弹窗
- 对可点击动作进行风险优先级排序
- 在安全边界内点击高优先级 CTA
- 向可见表单填入 fake data
- 保存每一步 URL 和截图
- 遇到年龄门槛或重复页面状态时停止

Action policy 会优先探索下载、领取奖励、注册、订阅、支付等更高风险路径，同时避免自动进入年龄受限内容。

#### 7.3 LLM 语义复核

规则系统擅长稳定信号提取，但不擅长理解页面真实语义。LLM 层用于：

- 页面意图分类
- 政策标签建议
- 语义层面的误报分析
- 面向审核员的总结
- 截图视觉证据观察

LLM 接收结构化证据，而不是无限制的原始网页内容：

```json
{
  "url": "...",
  "title": "...",
  "visible_text_excerpt": "...",
  "forms": [],
  "redirect_chain": [],
  "risk_term_evidence": {},
  "automation_steps": [],
  "rule_findings": []
}
```

模型输出结构化结果：

```json
{
  "page_intent": "adult_content",
  "policy_labels": ["Adult / Sexual Content"],
  "llm_risk_score": 75,
  "confidence": 0.9,
  "reviewer_summary": "...",
  "false_positive_assessment": [],
  "supporting_evidence": [],
  "visual_observations": []
}
```

#### 7.4 LLM 标签防幻觉机制

为了避免 LLM 生成没有依据的政策标签，系统加入 label guardrail：

- LLM 可以建议标签。
- 最终被接受的标签必须有规则证据或自动化信号支持。
- 没有证据支持的 LLM 标签会被拒绝，并进入误报提示。

示例：

```text
LLM suggested "Payment Collection", but no payment evidence was found.
Result: rejected_policy_labels = ["Payment Collection"]
```

这样既保留 LLM 的语义判断能力，又保证最终审核输出有证据支撑。

#### 7.5 截图视觉理解

部分风险内容可能出现在图片、弹窗、canvas 或视觉 banner 中。启用 LLM reasoning 时，系统会将 landing page 截图作为 image input 提供给模型。

该能力可以帮助识别：

- 图片中的警告文字
- 年龄门槛 UI
- 仅图片中存在的风险承诺
- DOM 未捕获的按钮文案
- 截图中可见的敏感内容

#### 7.6 Cloaking 和环境差异检测

系统会在多个环境中扫描同一个 URL：

- Desktop Chrome
- Mobile iPhone
- Ad-click referer

比较维度包括：

- 最终 URL
- 风险分数
- 文本相似度
- 下载按钮差异
- 表单或密码字段差异
- 截图

系统也预留了 geo cloaking 框架。真实 geo 检测需要地区代理，因为 locale 和 timezone 不能改变 IP 地理位置。

示例：

```text
US desktop → normal page
Indonesia mobile → APK download page
Result: high geo cloaking risk
```

### 8. 风险评分逻辑

系统采用混合决策框架：

```text
规则分数 = 确定性风险信号分数
LLM 分数 = 语义风险判断分数
最终分数 = 0.6 * 规则分数 + 0.4 * LLM 分数
```

如果 LLM 置信度较低，系统会降低 LLM 权重。

风险等级：

- Low: 0-39
- Medium: 40-69
- High: 70-100

系统同时输出置信度和误报提示，辅助审核员判断。

### 9. 评估指标

产品支持基于 labeled CSV 的评估流程。

核心指标：

- Precision：系统判为 risky 的页面中，真实 risky 的比例。
- Recall：真实 risky 页面中，被系统发现的比例。
- False positive rate：正常页面被误判为 risky 的比例。
- Manual review agreement rate：系统标签和人工审核标签的一致率。
- Risk discovery rate：动态路径模拟发现额外风险信号的比例。
- Average downstream depth：平均探索的后链路深度。
- Rejected LLM label rate：LLM 标签被 guardrail 拒绝的比例。

这些指标帮助产品和模型团队判断系统改动是否真的提升审核质量。

### 10. MVP 实现

当前技术栈：

- Python
- Playwright
- BeautifulSoup
- FastAPI
- Streamlit
- SQLite
- OpenAI Responses API with Structured Outputs

当前项目结构：

```text
ad-landing-risk-analyzer/
  backend/
    app/
      crawler/
      analyzer/
      automation/
      llm/
      evaluation/
      db/
  ui/
  storage/
  docs/
```

### 11. 迭代路线

V1：MVP 风险识别器

- URL 扫描
- 规则评分
- 证据提取
- Streamlit UI
- SQLite 历史记录

V2：自动化后链路探索

- 受控浏览器自动化
- CTA 优先级排序
- 表单填充
- 截图证据链
- 年龄门槛、登录墙、cookie 弹窗检测

V3：AI 审核层

- LLM 语义复核
- 截图视觉理解
- 标签防幻觉机制
- 混合分数融合
- 误报分析

V4：高级风险治理

- 多路径探索
- 对所有 downstream 截图做 OCR
- 接入真实地区代理池做 geo cloaking
- 审核员反馈闭环
- 相似风险页面聚类
- 政策阈值调优看板

### 12. 业务价值

该系统可以帮助商业安全团队：

- 提升广告后链路风险发现率
- 降低人工审核成本
- 提升政策判断一致性
- 为审核决策提供可复用证据
- 帮助策略团队量化政策影响
- 为 AI 模型改进沉淀结构化风险样本

这不是一个单纯技术 demo，而是一个面向广告审核风控业务的 AI 产品原型，覆盖业务问题定义、风险信号抽象、模型能力落地、评估体系设计和产品迭代规划。
