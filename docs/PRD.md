# PRD: AI-Assisted Ad Landing Page Risk Review System

## English Version

### 1. Product Context

In advertising review, downstream risk often appears after the user clicks the ad. A creative may look compliant, but the landing page can redirect to phishing forms, fake investment claims, forced downloads, sensitive content, or environment-specific cloaking pages.

The product opportunity is to help reviewers inspect landing pages faster and more consistently, while giving policy, risk operations, and AI teams structured evidence for governance and model improvement.

### 2. User Problem

Current manual review has several pain points:

- Reviewers must manually open links, inspect redirects, check forms, and capture evidence.
- Risk may only appear after user interaction or under mobile, ad referer, or geo-specific conditions.
- Review decisions can vary because evidence collection is not standardized.
- Policy teams have limited visibility into repeated downstream risk patterns.
- AI/model teams lack structured, evidence-backed samples for training and evaluation.

### 3. Target Users

- Primary user: ad reviewer.
- Secondary users: risk operations, policy team, AI/model team, data team, risk PM.

User needs:

- Ad reviewers need fast evidence collection and explainable risk reasons.
- Risk operations need consistent workflows and quality monitoring.
- Policy teams need structured examples for enforcement guidelines.
- AI/model teams need labeled evidence and false-positive cases.
- PMs need metrics to evaluate whether the product improves review quality.

### 4. Goals and Non-Goals

Product goals:

- Reduce manual review effort for landing page inspection.
- Increase downstream risk discovery.
- Provide evidence-backed risk labels instead of black-box decisions.
- Support reviewer trust through screenshots, redirect chains, form evidence, matched context, and false-positive notes.
- Create a measurable feedback loop for policy and AI improvements.

Non-goals for MVP:

- Fully automated enforcement with no human review.
- Malware binary reverse engineering.
- Payment transaction monitoring.
- Copyright ownership verification.
- Real geo cloaking detection without regional proxy infrastructure.

### 5. MVP Requirements

#### 5.1 URL Scan

Reviewer can submit a landing page URL and receive a structured scan result.

Requirements:

- Normalize and validate URL.
- Open page using browser automation.
- Capture final URL and redirect chain.
- Save screenshot.
- Persist scan result for later review.

#### 5.2 Evidence Extraction

The system extracts reviewer-facing evidence.

Requirements:

- Page title and visible text.
- Hidden text blocks.
- Links and destination URLs.
- Forms and input fields.
- Password and phone field detection.
- Download CTA and forced-download detection.
- Risk term matches with context snippets.

#### 5.3 Risk Scoring and Labels

The system provides an explainable baseline score.

Requirements:

- Convert extracted signals into risk score, risk level, policy labels, reasons, and confidence.
- Show evidence for every major finding.
- Add false-positive notes for weak or ambiguous signals.
- Cap score at 100 and use Low, Medium, High levels.

#### 5.4 Optional Dynamic Exploration

The system can simulate limited downstream user behavior.

Requirements:

- Scroll page.
- Detect candidate CTA buttons.
- Prioritize risky actions such as download, claim, register, subscribe, payment, or sign up.
- Fill fake data only into safe visible forms.
- Stop around age gates or repeated states.
- Save downstream URLs and screenshots.

#### 5.5 Optional LLM Semantic Review

The LLM layer supports reviewer interpretation, not direct enforcement.

Requirements:

- Send structured evidence, not raw unbounded page content.
- Return page intent, suggested policy labels, risk score, confidence, reviewer summary, false-positive assessment, and supporting evidence.
- Apply label guardrails so unsupported LLM labels are rejected or flagged.
- Blend rule score and LLM score only when confidence is sufficient.

#### 5.6 Optional Cloaking Check

The system can compare page behavior across environments.

Requirements:

- Scan desktop, mobile, and ad-referer contexts.
- Compare final URL, text similarity, download signals, form signals, risk score, and screenshots.
- Support geo cloaking framework when real regional proxies are configured.

### 6. Reviewer Workflow

```text
Reviewer submits landing page URL
-> System crawls page and captures evidence
-> System produces risk score, labels, confidence, and reasons
-> Reviewer inspects evidence and screenshot
-> Reviewer decides approve, reject, or escalate
-> Scan is saved for quality analysis and policy/model feedback
```

### 7. Success Metrics

Product metrics:

- Review time per landing page.
- Risk discovery rate.
- Evidence completeness rate.
- Manual reviewer agreement rate.
- Escalation rate to policy team.
- Reviewer adoption rate.

Quality metrics:

- Precision.
- Recall.
- False positive rate.
- False negative review sampling rate.
- Unsupported LLM label rejection rate.
- Average downstream exploration depth.

Operational metrics:

- Scan success rate.
- Timeout rate.
- Average scan latency.
- Screenshot capture success rate.
- LLM fallback rate.

### 8. Cross-Functional Execution Plan

Policy team:

- Define risk categories and enforcement labels.
- Review false-positive examples.
- Set escalation guidelines.

Review operations:

- Validate whether evidence format fits reviewer workflow.
- Provide manual labels for evaluation.
- Identify high-friction review scenarios.

Engineering:

- Build browser crawl, extraction, scoring, storage, and UI.
- Implement safe dynamic exploration boundaries.
- Monitor scan reliability and latency.

AI/model team:

- Design structured LLM output.
- Add guardrails against unsupported labels.
- Use reviewer feedback for prompt and model evaluation.

Data team:

- Maintain labeled CSV or dataset.
- Define metric calculation and reporting.
- Track changes across product iterations.

Legal/privacy:

- Review automated interaction boundaries.
- Approve fake data usage.
- Define screenshot and scan data retention expectations.

### 9. Product Tradeoffs

Rule baseline vs LLM-only:

- Decision: start with rule-based scoring and use LLM as an assistive layer.
- Reason: reviewers and policy teams need explainability and evidence traceability.

Recall vs false positives:

- Decision: expose score, confidence, evidence, and false-positive notes.
- Reason: early product should help reviewers calibrate rather than silently enforce.

Automation depth vs safety:

- Decision: controlled downstream exploration with stopping rules.
- Reason: automated clicking can create safety, privacy, or policy risks if unbounded.

MVP speed vs real geo coverage:

- Decision: build geo framework but require real proxies for true geo cloaking.
- Reason: locale and timezone changes do not prove regional content differences.

Reviewer trust vs full automation:

- Decision: support human decision-making first.
- Reason: policy enforcement requires auditability and reviewer confidence.

### 10. Current Implementation

Current stack:

- Python.
- Playwright.
- BeautifulSoup.
- FastAPI.
- Streamlit.
- SQLite.
- Optional OpenAI Structured Outputs.

Repository structure:

```text
backend/app/main.py                 API layer
backend/app/scanner.py              scan orchestration
backend/app/crawler/browser.py      browser crawl and screenshots
backend/app/crawler/extractor.py    DOM and text extraction
backend/app/analyzer/rules.py       risk scoring
backend/app/automation/flow_runner.py dynamic exploration
backend/app/analyzer/cloaking.py    environment mismatch checks
backend/app/llm/policy_reasoner.py  LLM semantic review
backend/app/evaluation/metrics.py   evaluation metrics
ui/streamlit_app.py                 reviewer-facing UI
```

### 11. Roadmap

V1: Evidence-backed MVP

- URL scan.
- Rule score.
- Evidence extraction.
- Screenshot capture.
- Scan history.
- Basic evaluation metrics.

V2: Reviewer workflow improvement

- Better evidence grouping.
- Reviewer decision capture.
- Feedback collection for false positives and false negatives.
- Policy escalation workflow.

V3: AI-assisted semantic review

- LLM summaries.
- Screenshot vision.
- Guardrailed policy labels.
- Hybrid scoring.
- Reviewer-facing false-positive explanation.

V4: Advanced risk governance

- Multi-path downstream exploration.
- OCR over screenshots.
- Real geo cloaking with proxy pool.
- Cluster similar risky pages.
- Threshold tuning dashboard.
- Model improvement feedback loop.

---

## 中文版

### 1. 产品背景

在广告审核中，风险经常出现在用户点击广告之后。广告素材本身可能看起来合规，但 landing page 可能跳转到钓鱼表单、虚假投资承诺、强制下载、敏感内容，或者基于设备和访问环境展示不同内容的 cloaking 页面。

这个产品机会在于：帮助审核员更快、更一致地检查落地页，同时为政策、风控运营和 AI 团队提供结构化证据，用于治理和模型改进。

### 2. 用户问题

当前人工审核有几个痛点：

- 审核员需要手动打开链接、检查跳转、查看表单并截图留证。
- 风险可能只在交互后，或在 mobile、ad referer、特定地区访问时出现。
- 因为证据收集不标准，审核决策容易不一致。
- 政策团队很难系统性看到重复出现的后链路风险模式。
- AI/模型团队缺少带证据的结构化样本来训练和评估模型。

### 3. 目标用户

- 主要用户：广告审核员。
- 次要用户：风控运营、政策团队、AI/模型团队、数据团队、风控产品经理。

用户需求：

- 广告审核员需要快速收集证据和可解释的风险原因。
- 风控运营需要一致的审核流程和质量监控。
- 政策团队需要结构化案例来完善执行标准。
- AI/模型团队需要标注证据和误报案例。
- PM 需要指标来判断产品是否真的提升审核质量。

### 4. 目标和非目标

产品目标：

- 降低 landing page 检查的人工审核成本。
- 提升后链路风险发现率。
- 提供有证据支撑的风险标签，而不是黑盒判断。
- 通过截图、跳转链、表单证据、上下文命中和误报提示建立审核员信任。
- 为政策和 AI 改进建立可量化反馈闭环。

MVP 非目标：

- 无人工参与的全自动处罚。
- 恶意文件二进制逆向。
- 支付交易监控。
- 版权归属验证。
- 在没有地区代理基础设施时做真实 geo cloaking 检测。

### 5. MVP 需求

#### 5.1 URL 扫描

审核员可以提交 landing page URL，并获得结构化扫描结果。

需求：

- URL 标准化和校验。
- 使用浏览器自动化打开页面。
- 捕获最终 URL 和跳转链。
- 保存截图。
- 持久化扫描结果，方便后续复查。

#### 5.2 证据提取

系统提取面向审核员的证据。

需求：

- 页面标题和可见文本。
- 隐藏文本块。
- 链接和目标 URL。
- 表单和输入字段。
- 密码字段和手机号字段检测。
- 下载 CTA 和强制下载检测。
- 风险词命中和上下文片段。

#### 5.3 风险评分和标签

系统提供可解释的 baseline 风险分。

需求：

- 将提取信号转换为风险分、风险等级、政策标签、原因和置信度。
- 每个主要 finding 都要展示证据。
- 对弱信号或模糊信号增加误报提示。
- 风险分最高 100，并分为 Low、Medium、High。

#### 5.4 可选动态探索

系统可以模拟有限的后链路用户行为。

需求：

- 滚动页面。
- 识别候选 CTA。
- 优先点击 download、claim、register、subscribe、payment、sign up 等高风险动作。
- 只在安全可见表单中填写 fake data。
- 遇到年龄门槛或重复页面状态时停止。
- 保存后续 URL 和截图。

#### 5.5 可选 LLM 语义复核

LLM 层用于帮助审核员理解页面语义，不直接做最终处罚。

需求：

- 输入结构化证据，而不是无限制的原始网页内容。
- 输出页面意图、建议政策标签、风险分、置信度、审核员总结、误报分析和支持证据。
- 应用标签 guardrail，没有证据支持的 LLM 标签需要被拒绝或标记。
- 只有在置信度足够时，才融合规则分和 LLM 分。

#### 5.6 可选 Cloaking 检测

系统可以比较不同环境下的页面行为。

需求：

- 扫描 desktop、mobile 和 ad-referer 环境。
- 对比最终 URL、文本相似度、下载信号、表单信号、风险分和截图。
- 在配置真实地区代理时支持 geo cloaking 框架。

### 6. 审核员工作流

```text
审核员提交 landing page URL
-> 系统抓取页面并捕获证据
-> 系统输出风险分、标签、置信度和原因
-> 审核员查看证据和截图
-> 审核员决定通过、拒绝或升级
-> 扫描结果保存，用于质量分析和政策/模型反馈
```

### 7. 成功指标

产品指标：

- 单个 landing page 审核耗时。
- 风险发现率。
- 证据完整率。
- 人工审核一致率。
- 升级到政策团队的比例。
- 审核员使用率。

质量指标：

- Precision。
- Recall。
- False positive rate。
- False negative 抽检率。
- LLM 无证据标签拒绝率。
- 平均后链路探索深度。

运营指标：

- 扫描成功率。
- 超时率。
- 平均扫描延迟。
- 截图成功率。
- LLM fallback rate。

### 8. 跨团队执行计划

政策团队：

- 定义风险类别和执行标签。
- 复核误报案例。
- 设定升级审核标准。

审核运营：

- 验证证据格式是否符合审核流程。
- 提供人工标签用于评估。
- 识别高摩擦审核场景。

工程团队：

- 建设浏览器抓取、信号提取、评分、存储和 UI。
- 实现安全的动态探索边界。
- 监控扫描可靠性和延迟。

AI/模型团队：

- 设计结构化 LLM 输出。
- 增加无证据标签的 guardrail。
- 使用审核反馈评估 prompt 和模型。

数据团队：

- 维护标注 CSV 或数据集。
- 定义指标计算和报告方式。
- 追踪产品迭代前后的指标变化。

法务/隐私：

- 评估自动化交互边界。
- 审批 fake data 使用方式。
- 定义截图和扫描数据保留预期。

### 9. 产品取舍

规则 baseline vs 纯 LLM：

- 决策：先用规则评分，LLM 作为辅助语义层。
- 原因：审核员和政策团队需要可解释性和证据可追溯。

召回率 vs 误报：

- 决策：展示分数、置信度、证据和误报提示。
- 原因：早期产品应帮助审核员校准，而不是静默执行处罚。

自动化深度 vs 安全边界：

- 决策：使用带停止规则的受控后链路探索。
- 原因：无边界自动点击可能带来安全、隐私或政策风险。

MVP 速度 vs 真实 geo 覆盖：

- 决策：建设 geo 框架，但真实 geo cloaking 需要真实代理。
- 原因：locale 和 timezone 变化不能证明地区内容差异。

审核员信任 vs 全自动化：

- 决策：第一版优先支持人工决策。
- 原因：政策执行需要可审计性和审核员信心。

### 10. 当前实现

当前技术栈：

- Python。
- Playwright。
- BeautifulSoup。
- FastAPI。
- Streamlit。
- SQLite。
- 可选 OpenAI Structured Outputs。

代码结构：

```text
backend/app/main.py                 API 层
backend/app/scanner.py              扫描流程编排
backend/app/crawler/browser.py      浏览器抓取和截图
backend/app/crawler/extractor.py    DOM 和文本提取
backend/app/analyzer/rules.py       风险评分
backend/app/automation/flow_runner.py 动态探索
backend/app/analyzer/cloaking.py    环境差异检测
backend/app/llm/policy_reasoner.py  LLM 语义复核
backend/app/evaluation/metrics.py   评估指标
ui/streamlit_app.py                 面向审核员的 UI
```

### 11. 路线图

V1: 有证据支撑的 MVP

- URL 扫描。
- 规则分。
- 证据提取。
- 截图。
- 扫描历史。
- 基础评估指标。

V2: 审核员工作流优化

- 更好的证据分组。
- 审核员决策记录。
- 误报和漏报反馈收集。
- 政策升级流程。

V3: AI 辅助语义复核

- LLM 总结。
- 截图视觉理解。
- 带 guardrail 的政策标签。
- 混合评分。
- 面向审核员的误报解释。

V4: 高级风险治理

- 多路径后链路探索。
- 截图 OCR。
- 基于代理池的真实 geo cloaking。
- 相似风险页面聚类。
- 阈值调优看板。
- 模型改进反馈闭环。
