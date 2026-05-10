# AI Ad Landing Page Risk Analyzer

An MVP risk-governance project for international advertising downstream review. It crawls an ad landing page, extracts page and browser signals, and produces an explainable risk score.

## Current MVP

- URL input and Playwright browser crawl
- Page title, visible text, hidden text, links, forms, redirect chain
- Password, phone, download, forced-download, suspicious-domain detection
- Payment / crypto / investment keyword matching
- Explainable rule-based risk score
- Tiered policy lexicons with high / medium / low confidence terms
- Context snippets for every matched risk term
- Basic negation filtering, for example "no crypto" is not treated as crypto promotion
- Multi-signal combinations, such as financial terms plus earnings claims
- False-positive notes for reviewer calibration
- Evaluation metrics from labeled review data: precision, recall, false positive rate, manual agreement, risk discovery rate, and average downstream depth
- Optional LLM semantic review layer using OpenAI Structured Outputs
- Optional multi-environment cloaking check across desktop, mobile, and ad-referer contexts
- Optional geo cloaking framework using real regional proxies configured in `storage/geo_environments.json`
- Optional controlled browser automation: scroll, click common CTAs, fill fake form data, save screenshots and URLs
- FastAPI backend, Streamlit UI, SQLite scan history

## Risk Rules

- Too many redirects: +20
- Password field: +25
- Crypto / investment / payment wording: +20
- Hidden text: +15
- Suspicious domain: +20
- Download behavior: +30
- Phone collection: +10
- Other form collection: +5

Scores are capped at 100.

## Setup

```bash
cd /Users/angelren/ad-landing-risk-analyzer
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

## Run API

```bash
cd /Users/angelren/ad-landing-risk-analyzer
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

## Run UI

```bash
cd /Users/angelren/ad-landing-risk-analyzer
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

## Verify Playwright

```bash
cd /Users/angelren/ad-landing-risk-analyzer
source .venv/bin/activate
python test_playwright.py
```

Expected output:

```text
ok
Hello Playwright
```

## Product Positioning

This should be presented as an ad downstream risk analysis system, not just a crawler. The system defines risk signals, turns them into a quantifiable score, preserves reviewer evidence, and can be extended with LLM-based semantic policy labeling.

Recommended next iteration:

- Add LLM policy classification labels: phishing, financial scam, crypto investment, forced download, data collection, misleading redirect
- Add OCR over screenshots for text rendered outside HTML
- Add clustering over historical risky pages
- Add reviewer feedback to tune rule weights and model prompts
