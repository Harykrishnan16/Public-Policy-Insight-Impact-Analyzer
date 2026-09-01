# Bill Simplifier

An AI-powered dashboard that turns dense Government Bills into plain-language,
citizen-friendly summaries — with sector impact analysis, a timeline of the
bill's history, and a downloadable PDF report.

Built to match the "Deployment (Streamlit / Gradio Dashboard)" spec:
- Upload Bill PDF / Paste URL
- AI Summary Panel
- Timeline view of bill history
- Industry Impact Data / Visual
- Downloadable Summary in PDF form

## 1. Setup env 


```bash
cd bill_simplifier
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run

```bash
streamlit run app.py
```

This opens the dashboard at `http://localhost:8501`.

## 3. Using it

You have three input options in the sidebar:

1. **Try a demo bill** — explore two pre-loaded, fully analyzed sample bills
   with no API key required (Registration of Births and Deaths (Amendment)
   Bill, 2026 and Taxation and Other Laws (Amendment) Bill, 2026).
2. **Upload PDF** — upload any Bill PDF from your computer.
3. **Paste URL** — paste a direct link to a Bill PDF, or an official bill
   page. Requires an Anthropic API key (enter it in the sidebar) since the
   text is sent to Claude for analysis.

Click **Analyze Bill**, then explore the tabs:
- **AI Summary** — plain-language explanation, objective, positives/negatives,
  short/medium/long-term impact forecast
- **Timeline** — chronology of the bill and related prior Acts
- **Industry Impact** — sector-by-sector impact chart, stakeholders, risks &
  opportunities
- **Full Details** — key provisions and the raw structured JSON
- **Download** — get a formatted PDF report or the raw JSON

## 4. Notes on reliability

Government portals such as `sansad.in` intermittently return server errors
or block automated requests. If a pasted URL fails to fetch:
1. Download the PDF manually in your browser.
2. Use the **Upload PDF** option instead.

For very long bills, the app truncates extremely long text (keeping the
beginning and end, which usually carry the "Statement of Objects and
Reasons" and key schedules) before sending it to the model, to stay within
context limits.

## 5. Architecture

```
bill_simplifier/
├── app.py              # Streamlit UI (5 tabs)
├── bill_analyzer.py     # PDF/URL text extraction + Claude API call + demo data
├── pdf_export.py         # ReportLab-based PDF report generator
├── requirements.txt
└── README.md
```

`bill_analyzer.py` defines the exact JSON schema the model must return
(title, ministry, objective, key provisions, related acts, stakeholders,
affected industries, risks/opportunities, citizen summary, sector impact,
chronology, impact forecast, positives/negatives) — matching the platform's
"Structured JSON object" output spec.

## 6. Extending

- **Swap to Gradio**: the core logic in `bill_analyzer.py` and
  `pdf_export.py` is UI-agnostic — you can build a `gradio_app.py` that
  calls the same `analyze_bill_text()` / `build_pdf_report()` functions
  with Gradio's `Blocks` API instead of Streamlit.
- **Bill Topic Classifier**: currently folded into the single LLM call.
  For higher accuracy at scale, split into a dedicated classification step
  (e.g. a smaller/cheaper model call or a fine-tuned classifier) before the
  full analysis call.
- **Knowledge Graph / chronology linking**: the `related_previous_acts`
  and `chronology` fields are a good seed for building an actual graph
  (e.g. with `networkx`) linking bills → parent Acts → amendments over time.
- **Caching**: add a local cache (e.g. SQLite or a JSON store) keyed by
  bill URL/hash so re-visiting the same bill doesn't re-call the API.
