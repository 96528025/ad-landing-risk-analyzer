from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db.database import list_scans
from backend.app.evaluation.metrics import compute_metrics
from backend.app.scanner import normalize_url, run_scan


st.set_page_config(page_title="Ad Landing Page Risk Analyzer", layout="wide")

page = st.sidebar.radio("View", ["Scanner", "Evaluation Metrics"])

st.title("Ad Landing Page Risk Analyzer")
st.caption("Baseline scanner for ad downstream risk: redirects, hidden content, forms, downloads, and policy-risk wording.")

if page == "Evaluation Metrics":
    st.subheader("Evaluation Metrics")
    st.write("Use a labeled CSV to evaluate scan results saved in SQLite.")
    threshold = st.slider("Risk threshold", min_value=0, max_value=100, value=40, step=5)
    uploaded = st.file_uploader("Upload labels CSV", type=["csv"])
    default_label_path = ROOT / "storage" / "labels.example.csv"

    label_path = default_label_path
    if uploaded is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp:
            temp.write(uploaded.getvalue())
            label_path = Path(temp.name)

    st.caption(f"Using labels: {label_path}")
    metrics = compute_metrics(label_path, threshold=threshold)

    c1, c2, c3 = st.columns(3)
    c1.metric("Precision", f"{metrics['precision']:.2f}")
    c2.metric("Recall", f"{metrics['recall']:.2f}")
    c3.metric("False Positive Rate", f"{metrics['false_positive_rate']:.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Manual Agreement", f"{metrics['manual_review_agreement']:.2f}")
    c5.metric("Risk Discovery Rate", f"{metrics['risk_discovery_rate']:.2f}")
    c6.metric("Avg Downstream Depth", f"{metrics['average_downstream_depth']:.2f}")

    st.write("Confusion matrix:", metrics["confusion_matrix"])
    st.caption(f"Labeled URLs: {metrics['labeled_urls']} | Matched scans: {metrics['matched_scans']}")
    if metrics["rows"]:
        st.dataframe(metrics["rows"], use_container_width=True)
    else:
        st.info("No labeled URLs matched saved scans yet. Run scans for URLs in the label file or upload a matching CSV.")
    st.stop()

with st.form("scan_form"):
    url = st.text_input("Landing page URL", placeholder="https://example.com")
    dynamic = st.checkbox("Run controlled user simulation", value=False)
    cloaking = st.checkbox("Run multi-environment cloaking check", value=False)
    use_llm = st.checkbox("Use LLM semantic reasoning", value=False)
    submitted = st.form_submit_button("Scan")

if submitted and url:
    with st.spinner("Scanning landing page..."):
        try:
            normalized_url = normalize_url(url)
            result = asyncio.run(run_scan(normalized_url, dynamic=dynamic, use_llm=use_llm, cloaking=cloaking))
        except Exception as exc:
            st.error(f"Scan failed: {exc}")
            st.stop()

    risk = result.risk
    signals = result.signals
    st.caption(f"Scanned URL: {signals.requested_url}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", f"{risk.score} / 100")
    col2.metric("Risk Level", risk.level)
    col3.metric("Confidence", f"{risk.confidence:.2f}")
    st.caption(f"Redirects: {len(signals.redirect_chain)}")
    if risk.final_score is not None:
        st.metric("Final Hybrid Score", f"{risk.final_score} / 100", help="Rule score blended with LLM semantic score when available.")
        st.caption(f"Final Hybrid Level: {risk.final_level}")

    st.subheader("Reasons")
    for reason in risk.reasons:
        st.write(f"- {reason}")

    if risk.policy_labels:
        st.subheader("Policy Labels")
        st.write(", ".join(risk.policy_labels))

    if risk.findings:
        st.subheader("Evidence")
        for finding in risk.findings:
            with st.expander(
                f"{finding['policy_label']} | {finding['severity']} | +{finding['score_impact']} | confidence {finding.get('confidence', 0.0)}"
            ):
                st.write(finding["reason"])
                evidence = finding.get("evidence") or []
                if evidence:
                    st.write("Evidence:")
                    for item in evidence:
                        st.write(f"- {item}")

    if risk.false_positive_notes:
        st.subheader("False Positive Analysis")
        for note in risk.false_positive_notes:
            st.write(f"- {note}")

    if risk.llm_analysis:
        st.subheader("LLM Semantic Review")
        llm = risk.llm_analysis
        st.write("Status:", llm.get("status"))
        st.write("Page intent:", llm.get("page_intent"))
        st.write("LLM score:", llm.get("llm_risk_score"))
        st.write("LLM confidence:", llm.get("confidence"))
        st.write("Reviewer summary:", llm.get("reviewer_summary"))
        if llm.get("policy_labels"):
            st.write("LLM suggested labels:", ", ".join(llm["policy_labels"]))
        if llm.get("accepted_policy_labels"):
            st.write("Accepted labels:", ", ".join(llm["accepted_policy_labels"]))
        if llm.get("rejected_policy_labels"):
            st.write("Rejected labels:", ", ".join(llm["rejected_policy_labels"]))
        if llm.get("visual_observations"):
            with st.expander("LLM Visual Observations"):
                for item in llm["visual_observations"]:
                    st.write(f"- {item}")
        if llm.get("supporting_evidence"):
            with st.expander("LLM Supporting Evidence"):
                for item in llm["supporting_evidence"]:
                    st.write(f"- {item}")

    st.subheader("Extracted Signals")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Links", len(signals.links))
    c2.metric("Forms", len(signals.forms))
    c3.metric("Hidden Text Blocks", len(signals.hidden_text))
    c4.metric("Risk Terms", len(signals.matched_risk_terms))

    st.write("Final URL:", signals.final_url)
    if signals.risk_term_categories:
        st.write("Risk term categories:")
        for category, terms in signals.risk_term_categories.items():
            st.write(f"- {category}: {', '.join(terms)}")
    if signals.risk_term_evidence:
        with st.expander("Risk Term Context"):
            for category, items in signals.risk_term_evidence.items():
                st.write(f"**{category}**")
                for item in items:
                    st.write(
                        f"- {item['term']} | {item['tier']} | confidence {item['confidence']}: {item['context']}"
                    )
    elif signals.matched_risk_terms:
        st.write("Matched terms:", ", ".join(signals.matched_risk_terms))

    if signals.automation_signals:
        st.write("Automation signals:", ", ".join(signals.automation_signals))

    if signals.cloaking_analysis:
        cloaking_result = signals.cloaking_analysis
        st.subheader("Cloaking / Environment Mismatch")
        c1, c2 = st.columns(2)
        c1.metric("Cloaking Score", f"{cloaking_result['score']} / 100")
        c2.metric("Cloaking Level", cloaking_result["level"])
        st.write("Reasons:")
        for reason in cloaking_result["reasons"]:
            st.write(f"- {reason}")
        if cloaking_result.get("notes"):
            st.write("Notes:")
            for note in cloaking_result["notes"]:
                st.write(f"- {note}")
        with st.expander("Environment Summaries"):
            st.dataframe(
                [
                    {"environment": env, **summary}
                    for env, summary in cloaking_result["environment_summaries"].items()
                ],
                use_container_width=True,
            )
        with st.expander("Environment Comparisons"):
            st.dataframe(cloaking_result["comparisons"], use_container_width=True)
        with st.expander("Environment Screenshots"):
            for env, summary in cloaking_result["environment_summaries"].items():
                st.write(env)
                if summary.get("screenshot_path"):
                    st.image(summary["screenshot_path"], width=600)
        if cloaking_result.get("geo_analysis"):
            geo = cloaking_result["geo_analysis"]
            st.subheader("Geo Cloaking")
            if geo.get("status") == "skipped":
                st.info(geo.get("reason"))
            else:
                c1, c2 = st.columns(2)
                c1.metric("Geo Cloaking Score", f"{geo['score']} / 100")
                c2.metric("Geo Cloaking Level", geo["level"])
                st.write("Geo reasons:")
                for reason in geo["reasons"]:
                    st.write(f"- {reason}")
                if geo.get("notes"):
                    st.write("Geo notes:")
                    for note in geo["notes"]:
                        st.write(f"- {note}")
                with st.expander("Geo Environment Summaries"):
                    st.dataframe(
                        [
                            {"environment": env, **summary}
                            for env, summary in geo["environment_summaries"].items()
                        ],
                        use_container_width=True,
                    )
                with st.expander("Geo Environment Comparisons"):
                    st.dataframe(geo["comparisons"], use_container_width=True)

    with st.expander("Redirect Chain"):
        for item in signals.redirect_chain:
            st.write(item)

    with st.expander("Forms"):
        for form in signals.forms:
            st.json(form.model_dump())

    with st.expander("Hidden Text"):
        for text in signals.hidden_text:
            st.write(text)

    with st.expander("Links"):
        for link in signals.links[:100]:
            st.write(f"{link.text or '(no text)'} -> {link.href}")

    if signals.screenshot_path:
        st.subheader("Screenshot")
        st.image(signals.screenshot_path, width=900)

    if signals.automation_steps:
        st.subheader("Automation Steps")
        for step in signals.automation_steps:
            title = step.get("label", "step")
            url = step.get("url", "")
            with st.expander(f"{title} - {url}", expanded=title == "blocked_age_gate"):
                if step.get("detected_signals"):
                    st.write("Detected signals:", ", ".join(step["detected_signals"]))
                if step.get("blocked_reason"):
                    st.warning(step["blocked_reason"])
                if step.get("clicked"):
                    st.write("Clicked:", step["clicked"])
                if step.get("action_reason"):
                    st.write("Action reason:", step["action_reason"])
                if step.get("filled_fields"):
                    st.write("Filled fields:", ", ".join(step["filled_fields"]))
                if step.get("candidate_actions"):
                    st.write("Top candidate actions:")
                    for candidate in step["candidate_actions"][:5]:
                        unsafe = " unsafe" if candidate.get("unsafe") else ""
                        st.write(
                            f"- {candidate.get('text')} | priority {candidate.get('priority')} | {candidate.get('reason')}{unsafe}"
                        )
            if step.get("screenshot_path"):
                st.image(step["screenshot_path"], width=900)

st.sidebar.header("Recent Scans")
for scan in list_scans():
    st.sidebar.write(f"#{scan['id']} {scan['risk_level']} {scan['risk_score']} - {scan['requested_url']}")
