"""
Bill Simplifier -- Streamlit Dashboard
Run with:  streamlit run app.py

Features:
  - Upload a Bill PDF, or paste a URL (PDF link or bill page)
  - AI Summary Panel (citizen-friendly explanation)
  - Timeline view of the bill's chronology
  - Industry / Sector impact visual
  - Downloadable PDF summary
"""

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from bill_analyzer import (
    extract_text_from_pdf_bytes,
    fetch_url_text,
    analyze_bill_text,
    get_demo_bill,
    DEMO_BILLS,
)
from pdf_export import build_pdf_report

st.set_page_config(page_title="Bill Simplifier", page_icon="🏛️", layout="wide")

DIRECTION_COLORS = {
    "Positive": "#2a9d8f",
    "Negative": "#e76f51",
    "Mixed": "#e9c46a",
    "Neutral": "#8d99ae",
}


# ---------------------------------------------------------------------------
# Sidebar -- input controls
# ---------------------------------------------------------------------------

st.sidebar.title("🏛️ Bill Simplifier")
st.sidebar.caption("Understand any Government Bill in plain language.")

api_key = st.sidebar.text_input(
    "Anthropic API Key",
    type="password",
    help="Needed to analyze a new bill with AI. Leave blank to explore the two demo bills instead.",
)

input_mode = st.sidebar.radio("Input source", ["Try a demo bill", "Upload PDF", "Paste URL"])

uploaded_file = None
pasted_url = ""
selected_demo = None

if input_mode == "Upload PDF":
    uploaded_file = st.sidebar.file_uploader("Upload Bill PDF", type=["pdf"])
elif input_mode == "Paste URL":
    pasted_url = st.sidebar.text_input(
        "Bill URL (PDF link or bill page)",
        placeholder="https://sansad.in/getFile/BillsTexts/...pdf?source=legislation",
    )
else:
    selected_demo = st.sidebar.selectbox("Choose a sample bill", list(DEMO_BILLS.keys()))

run_button = st.sidebar.button("Analyze Bill", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Note: Some government portals (e.g. sansad.in) intermittently block or "
    "error on automated fetches. If a URL fails, download the PDF manually "
    "and use the Upload option instead."
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "source_note" not in st.session_state:
    st.session_state.source_note = ""


def run_analysis():
    try:
        if input_mode == "Try a demo bill":
            st.session_state.analysis = get_demo_bill(selected_demo)
            st.session_state.source_note = "Demo dataset (offline sample)"
            return

        if input_mode == "Upload PDF":
            if uploaded_file is None:
                st.sidebar.error("Please upload a PDF first.")
                return
            with st.spinner("Extracting text from PDF..."):
                text = extract_text_from_pdf_bytes(uploaded_file.read())
            st.session_state.source_note = f"Uploaded file: {uploaded_file.name}"

        elif input_mode == "Paste URL":
            if not pasted_url.strip():
                st.sidebar.error("Please paste a URL first.")
                return
            with st.spinner("Fetching document from URL..."):
                try:
                    text = fetch_url_text(pasted_url.strip())
                except Exception as fetch_err:
                    st.sidebar.error(
                        f"Could not fetch that URL ({fetch_err}). "
                        "Try downloading the PDF manually and using Upload instead."
                    )
                    return
            st.session_state.source_note = f"Fetched from URL: {pasted_url.strip()}"

        if not text or len(text.strip()) < 200:
            st.sidebar.error("Extracted text looks too short -- the document may be scanned/image-based or empty.")
            return

        if not api_key:
            st.sidebar.error("An API key is required to analyze a new document. Use 'Try a demo bill' to explore without one.")
            return

        with st.spinner("Analyzing bill with AI (this can take 20-40s for long bills)..."):
            analysis = analyze_bill_text(text, api_key)
        st.session_state.analysis = analysis

    except Exception as e:
        st.sidebar.error(f"Something went wrong: {e}")


if run_button:
    run_analysis()


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

analysis = st.session_state.analysis

if analysis is None:
    st.title("🏛️ Bill Simplifier")
    st.write(
        "Upload a Bill PDF, paste an official bill URL, or explore a demo bill "
        "from the sidebar to get a plain-language breakdown: what it does, who "
        "it affects, and what happens next."
    )
    st.info("👈 Choose an input source in the sidebar and click **Analyze Bill** to get started.")
    st.stop()

# --- Header -----------------------------------------------------------------
st.title(analysis.get("title", "Bill Summary"))
meta_cols = st.columns(4)
meta_cols[0].metric("Ministry", analysis.get("ministry") or "—")
meta_cols[1].metric("Introduced in", analysis.get("introduced_in") or "—")
meta_cols[2].metric("Lok Sabha passed", analysis.get("passed_lok_sabha_date") or "Pending")
meta_cols[3].metric("Rajya Sabha passed", analysis.get("passed_rajya_sabha_date") or "Pending")
st.caption(f"Source: {st.session_state.source_note}")

st.markdown("---")

tab_summary, tab_timeline, tab_impact, tab_details, tab_download = st.tabs(
    ["📝 AI Summary", "🕒 Timeline", "🏭 Industry Impact", "📋 Full Details", "⬇️ Download"]
)

# --- AI Summary Panel ---------------------------------------------------
with tab_summary:
    st.subheader("What This Means For You")
    st.write(analysis.get("citizen_summary", "No summary available."))

    st.subheader("Objective")
    st.write(analysis.get("objective", "—"))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Positives")
        for p in analysis.get("positives", []):
            st.markdown(f"- {p}")
    with col2:
        st.subheader("⚠️ Negatives")
        for n in analysis.get("negatives", []):
            st.markdown(f"- {n}")

    forecast = analysis.get("impact_forecast") or {}
    if forecast:
        st.subheader("Impact Forecast")
        f1, f2, f3 = st.columns(3)
        f1.markdown("**Short-term (0-1 yr)**")
        f1.write(forecast.get("short_term", "—"))
        f2.markdown("**Medium-term (1-5 yrs)**")
        f2.write(forecast.get("medium_term", "—"))
        f3.markdown("**Long-term (5+ yrs)**")
        f3.write(forecast.get("long_term", "—"))

# --- Timeline -------------------------------------------------------------
with tab_timeline:
    st.subheader("Bill History & Chronology")
    chronology = analysis.get("chronology", [])
    if chronology:
        df = pd.DataFrame(chronology)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Simple vertical timeline visual
        fig = go.Figure()
        y_positions = list(range(len(chronology)))[::-1]
        fig.add_trace(
            go.Scatter(
                x=[0] * len(chronology),
                y=y_positions,
                mode="markers+text",
                marker=dict(size=14, color="#16213e"),
                text=[c.get("date", "") for c in chronology],
                textposition="middle right",
                hovertext=[c.get("event", "") for c in chronology],
                hoverinfo="text",
            )
        )
        for i, c in enumerate(chronology):
            fig.add_annotation(
                x=0.05,
                y=y_positions[i],
                text=c.get("event", ""),
                showarrow=False,
                xanchor="left",
                font=dict(size=12),
                xref="x",
                yref="y",
            )
        fig.update_layout(
            showlegend=False,
            xaxis=dict(visible=False, range=[-0.1, 2]),
            yaxis=dict(visible=False),
            height=120 + 60 * len(chronology),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No chronology data available for this bill.")

    if analysis.get("related_previous_acts"):
        st.subheader("Related Previous Acts / Amendments")
        for act in analysis["related_previous_acts"]:
            st.markdown(f"- {act}")

# --- Industry Impact --------------------------------------------------------
with tab_impact:
    st.subheader("Sector / Industry Impact")
    sector_impact = analysis.get("sector_impact", [])
    if sector_impact:
        df = pd.DataFrame(sector_impact)
        df["score"] = df["direction"].map({"Positive": 1, "Mixed": 0.3, "Neutral": 0, "Negative": -1}).fillna(0)

        fig = px.bar(
            df,
            x="score",
            y="sector",
            color="direction",
            orientation="h",
            color_discrete_map=DIRECTION_COLORS,
            hover_data={"impact": True, "score": False},
            labels={"score": "Impact direction", "sector": "Sector"},
        )
        fig.update_layout(height=100 + 60 * len(df), xaxis=dict(range=[-1.2, 1.2], showticklabels=False))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df[["sector", "impact", "direction"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No sector impact data available for this bill.")

    if analysis.get("affected_industries"):
        st.subheader("Affected Industries")
        st.write(", ".join(analysis["affected_industries"]))

    if analysis.get("stakeholders"):
        st.subheader("Stakeholders")
        st.write(", ".join(analysis["stakeholders"]))

    ro = analysis.get("risks_and_opportunities") or {}
    if ro.get("risks") or ro.get("opportunities"):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Risks")
            for r in ro.get("risks", []):
                st.markdown(f"- {r}")
        with c2:
            st.subheader("Opportunities")
            for o in ro.get("opportunities", []):
                st.markdown(f"- {o}")

# --- Full Details / raw JSON ------------------------------------------------
with tab_details:
    st.subheader("Key Provisions")
    for kp in analysis.get("key_provisions", []):
        st.markdown(f"- {kp}")

    st.subheader("Raw Structured Output (JSON)")
    st.json(analysis)

# --- Download ---------------------------------------------------------------
with tab_download:
    st.subheader("Download This Analysis")

    pdf_bytes = build_pdf_report(analysis)
    st.download_button(
        label="⬇️ Download Summary as PDF",
        data=pdf_bytes,
        file_name=f"{analysis.get('title', 'bill_summary')[:60].replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.download_button(
        label="⬇️ Download Structured Data as JSON",
        data=json.dumps(analysis, indent=2),
        file_name=f"{analysis.get('title', 'bill_summary')[:60].replace(' ', '_')}.json",
        mime="application/json",
        use_container_width=True,
    )
