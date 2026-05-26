# PM Case Study: AI-Assisted Ad Landing Page Risk Review System

## English Version

### 1. Interview Summary

This project is a PM case for an AI-assisted ad downstream risk review system. The core user problem is that ad risk is not always visible in the creative. A landing page can reveal phishing, forced downloads, deceptive financial claims, sensitive content, or cloaking only after a user clicks the ad.

The product goal is to help reviewers collect evidence faster, make more consistent decisions, and create structured feedback for policy and AI teams.

### 2. Problem

Manual landing page review is slow and inconsistent because reviewers need to inspect redirects, page content, forms, screenshots, hidden text, device-specific behavior, and sometimes downstream clicks.

Key pain points:

- Reviewers spend time collecting evidence manually.
- Risky behavior may appear only after redirects or user interaction.
- Review decisions are hard to audit if evidence is not standardized.
- Rule-only detection can create false positives.
- LLM-only detection can create unsupported labels.

### 3. Users

Primary user:

- Ad reviewer: needs clear evidence to approve, reject, or escalate an ad.

Secondary users:

- Policy team: needs structured cases to refine policy definitions.
- Risk operations: needs consistent workflows and quality metrics.
- AI/model team: needs evidence-backed examples for model improvement.
- Data team: needs labeled data and evaluation metrics.
- PM: needs to balance accuracy, trust, operational cost, and execution feasibility.

### 4. Product Hypothesis

If we automatically extract landing page evidence and present an explainable risk summary, then reviewers can make faster and more consistent decisions while policy and AI teams gain better structured feedback.

### 5. MVP Definition

The MVP focuses on evidence-backed review assistance, not fully automated enforcement.

MVP includes:

- URL submission.
- Landing page crawl.
- Redirect chain capture.
- Screenshot capture.
- Form, link, hidden text, and download signal extraction.
- Risk term matching with context.
- Explainable risk score and policy labels.
- False-positive notes.
- Scan history.
- Evaluation metrics from labeled data.

Optional advanced capabilities:

- Controlled downstream automation.
- LLM semantic review with structured output.
- Cloaking detection across desktop, mobile, and ad-referer contexts.

### 6. Why This MVP

I would prioritize reviewer evidence first because trust is the core adoption barrier. If reviewers do not understand why the system flags a landing page, they will not rely on it.

I would start with rule-based scoring because it is auditable and easy for policy teams to validate. LLM is useful for semantic interpretation, but it should be constrained by evidence guardrails before it influences review outcomes.

### 7. Cross-Functional Execution

Policy team:

- Define risk categories such as phishing, financial scam, forced download, adult content, hidden content, and misleading redirect.
- Review ambiguous examples and false positives.

Review operations:

- Validate whether the evidence view fits the actual reviewer workflow.
- Provide labeled examples and reviewer feedback.

Engineering:

- Build the crawler, extractor, scoring pipeline, storage, and reviewer UI.
- Add reliability monitoring for timeouts and scan failures.

AI/model team:

- Design structured LLM review outputs.
- Add guardrails so unsupported labels are rejected.
- Evaluate whether LLM summaries reduce reviewer effort.

Data team:

- Maintain labeled evaluation data.
- Track precision, recall, false positive rate, and reviewer agreement.

Legal/privacy:

- Review fake data usage in automated form filling.
- Define boundaries for screenshots, stored content, and automated interactions.

### 8. Metrics

Product success metrics:

- Review time per landing page.
- Reviewer adoption rate.
- Evidence completeness rate.
- Manual reviewer agreement rate.
- Escalation rate to policy team.

Risk quality metrics:

- Risk discovery rate.
- Precision.
- Recall.
- False positive rate.
- False negative sampling rate.

System metrics:

- Scan success rate.
- Timeout rate.
- Average scan latency.
- Screenshot success rate.

AI metrics:

- LLM label acceptance rate.
- Unsupported LLM label rejection rate.
- Reviewer usefulness rating for LLM summaries.

### 9. Product Tradeoffs

Rule-based scoring vs LLM-only:

- I chose rule-based baseline first because reviewers and policy teams need explainable evidence. LLM is added as a semantic assistant, not as the only decision-maker.

High recall vs false positives:

- In early review tools, high recall can help discover risk, but false positives create reviewer fatigue. The product should show confidence and evidence so reviewers can calibrate.

Automation depth vs safety:

- The system should not blindly click every button or submit real user data. Controlled exploration with fake data and stop conditions is safer.

Fast MVP vs full geo cloaking:

- Real geo cloaking needs proxy infrastructure. The MVP can define the framework and compare available environments first.

Automation vs reviewer trust:

- The first version should assist human decisions. Full automation can come later only after quality metrics and trust are strong.

### 10. Roadmap

Phase 1: Evidence-backed scan

- URL scan, screenshot, redirect chain, forms, links, hidden text, download signal, rule score.

Phase 2: Reviewer workflow

- Decision capture, feedback buttons, evidence grouping, policy escalation flow.

Phase 3: AI assistance

- LLM summary, semantic policy labels, screenshot vision, label guardrails.

Phase 4: Risk intelligence

- Similar landing page clustering, trend dashboard, threshold tuning, model feedback loop.

### 11. Interview Talk Track

Short version:

> I designed this as an AI-assisted downstream ad review product. The problem is that risky behavior often appears after the ad click, not in the creative itself. The MVP helps reviewers collect landing page evidence, see an explainable risk score, and make faster approve, reject, or escalate decisions. I intentionally started with evidence-backed rules for reviewer trust, then added LLM semantic review with guardrails as an assistive layer.

Longer version:

> My primary user was the ad reviewer, but the product also served policy, risk operations, and AI teams. Reviewers needed speed and clear evidence. Policy teams needed structured examples. AI teams needed evidence-backed samples to improve models. The MVP focused on URL scanning, screenshot capture, redirect chain, form and download detection, risk labels, and evaluation metrics. The major product tradeoff was between automation and trust, so I designed the system to support human review first rather than fully automate enforcement.

---

## 中文版

### 1. 面试总结

这个项目可以作为一个 AI 辅助广告后链路风险审核系统的 PM case。核心用户问题是：广告风险不一定出现在广告素材本身，很多风险只有在用户点击广告进入 landing page 后才出现，例如钓鱼、强制下载、虚假金融承诺、敏感内容或 cloaking。

产品目标是帮助审核员更快收集证据、更一致地做判断，同时为政策和 AI 团队沉淀结构化反馈。

### 2. 问题

人工 landing page 审核速度慢且一致性弱，因为审核员需要检查跳转、页面内容、表单、截图、隐藏文本、设备差异，有时还需要继续点击后链路。

核心痛点：

- 审核员需要手动收集证据，耗时高。
- 风险行为可能只在跳转或用户交互后出现。
- 如果证据没有标准化，审核决策很难追溯。
- 纯规则检测容易误报。
- 纯 LLM 检测可能生成没有证据支持的标签。

### 3. 用户

主要用户：

- 广告审核员：需要清晰证据来决定通过、拒绝或升级审核。

次要用户：

- 政策团队：需要结构化案例来完善政策定义。
- 风控运营：需要一致的流程和质量指标。
- AI/模型团队：需要带证据的样本来改进模型。
- 数据团队：需要标注数据和评估指标。
- PM：需要平衡准确率、信任、运营成本和执行可行性。

### 4. 产品假设

如果系统可以自动提取 landing page 证据，并展示可解释的风险总结，那么审核员可以更快、更一致地做判断，同时政策和 AI 团队也能获得更好的结构化反馈。

### 5. MVP 定义

MVP 聚焦于有证据支撑的审核辅助，而不是全自动处罚。

MVP 包含：

- URL 提交。
- Landing page 抓取。
- 跳转链捕获。
- 截图保存。
- 表单、链接、隐藏文本和下载信号提取。
- 风险词上下文匹配。
- 可解释风险分和政策标签。
- 误报提示。
- 扫描历史。
- 基于标注数据的评估指标。

可选高级能力：

- 受控后链路自动化。
- 带结构化输出的 LLM 语义复核。
- 基于 desktop、mobile 和 ad-referer 的 cloaking 检测。

### 6. 为什么这样定义 MVP

我会优先做 reviewer evidence，因为信任是采用这个产品的核心门槛。如果审核员看不懂系统为什么标记一个 landing page，他们就不会依赖这个系统。

我会先用规则评分，因为规则更可审计，也更容易让政策团队验证。LLM 对语义理解有帮助，但在影响审核结果之前，必须被证据 guardrail 约束。

### 7. 跨团队执行

政策团队：

- 定义 phishing、financial scam、forced download、adult content、hidden content、misleading redirect 等风险类别。
- 复核模糊案例和误报案例。

审核运营：

- 验证证据视图是否符合真实审核流程。
- 提供标注样本和审核员反馈。

工程团队：

- 建设 crawler、extractor、scoring pipeline、storage 和 reviewer UI。
- 增加 timeout 和 scan failure 的可靠性监控。

AI/模型团队：

- 设计结构化 LLM 审核输出。
- 增加 guardrail，拒绝没有证据支持的标签。
- 评估 LLM 总结是否减少审核员工作量。

数据团队：

- 维护标注评估数据。
- 追踪 precision、recall、false positive rate 和 reviewer agreement。

法务/隐私：

- 评估自动化填表中 fake data 的使用。
- 定义截图、页面内容存储和自动化交互边界。

### 8. 指标

产品成功指标：

- 单个 landing page 审核耗时。
- 审核员使用率。
- 证据完整率。
- 人工审核一致率。
- 升级到政策团队的比例。

风险质量指标：

- 风险发现率。
- Precision。
- Recall。
- False positive rate。
- False negative 抽检率。

系统指标：

- 扫描成功率。
- 超时率。
- 平均扫描延迟。
- 截图成功率。

AI 指标：

- LLM 标签接受率。
- LLM 无证据标签拒绝率。
- 审核员对 LLM 总结的有用性评分。

### 9. 产品取舍

规则评分 vs 纯 LLM：

- 我选择先做规则 baseline，因为审核员和政策团队需要可解释证据。LLM 作为语义辅助，而不是唯一决策者。

高召回 vs 误报：

- 早期审核工具中，高召回有助于发现风险，但误报会造成审核疲劳。产品应该展示置信度和证据，让审核员校准判断。

自动化深度 vs 安全：

- 系统不应该盲目点击所有按钮或提交真实用户数据。使用 fake data 和停止条件的受控探索更安全。

快速 MVP vs 完整 geo cloaking：

- 真实 geo cloaking 需要代理基础设施。MVP 可以先定义框架，并比较已有环境。

自动化 vs 审核员信任：

- 第一版应该辅助人工决策。只有当质量指标和信任足够强之后，才考虑更高程度自动化。

### 10. 路线图

Phase 1: 有证据的扫描

- URL 扫描、截图、跳转链、表单、链接、隐藏文本、下载信号、规则评分。

Phase 2: 审核员工作流

- 决策记录、反馈按钮、证据分组、政策升级流程。

Phase 3: AI 辅助

- LLM 总结、语义政策标签、截图视觉理解、标签 guardrail。

Phase 4: 风险智能

- 相似 landing page 聚类、趋势看板、阈值调优、模型反馈闭环。

### 11. 面试讲法

短版本：

> 我把这个项目设计成一个 AI 辅助广告后链路审核产品。问题是很多广告风险不在素材本身，而是在点击后的 landing page 才出现。MVP 帮助审核员收集落地页证据、看到可解释风险分，并更快做出通过、拒绝或升级判断。我有意先用证据支撑的规则建立审核员信任，再加入带 guardrail 的 LLM 语义复核作为辅助层。

长版本：

> 我的主要用户是广告审核员，但这个产品也服务政策、风控运营和 AI 团队。审核员需要速度和清晰证据，政策团队需要结构化案例，AI 团队需要带证据的样本来改进模型。MVP 聚焦 URL 扫描、截图、跳转链、表单和下载检测、风险标签和评估指标。最大的产品取舍是自动化和信任之间的平衡，所以我先把系统设计成人工审核辅助，而不是直接做全自动处罚。
