"""
bill_analyzer.py
Core logic for the Bill Simplifier platform:
  - Extract text from an uploaded PDF or a URL (PDF or HTML page)
  - Call an LLM (Anthropic Claude) to produce a structured JSON analysis
    matching the platform's output schema
  - Provide a offline demo/fallback dataset for the two sample bills so the
    dashboard can be explored without an API key or network access

Swap ANALYZE_WITH_LLM = False to always use the offline demo data.
"""

import io
import json
import re
from datetime import datetime

import requests

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


MODEL_NAME = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a legislative analyst for a citizen-facing platform \
that explains government Bills in plain language. You will be given the raw \
text of a Bill (or a partial excerpt if the document is very long). \
Return ONLY a single valid JSON object -- no markdown fences, no preamble, \
no commentary -- matching exactly this schema:

{
  "title": string,
  "ministry": string,
  "introduced_in": string,
  "introduction_date": string or null (YYYY-MM-DD if known, else null),
  "passed_lok_sabha_date": string or null,
  "passed_rajya_sabha_date": string or null,
  "objective": string (2-4 sentences),
  "key_provisions": [string, ...]  (5-8 bullet points),
  "related_previous_acts": [string, ...],
  "stakeholders": [string, ...],
  "affected_industries": [string, ...],
  "risks_and_opportunities": {
    "risks": [string, ...],
    "opportunities": [string, ...]
  },
  "citizen_summary": string (10-20 lines, 8th-grade reading level, explains \
what the bill means for an ordinary person),
  "sector_impact": [
    {"sector": string, "impact": string, "direction": "Positive"|"Negative"|"Mixed"|"Neutral"}
  ],
  "chronology": [
    {"date": string, "event": string}
  ],
  "impact_forecast": {
    "short_term": string,
    "medium_term": string,
    "long_term": string
  },
  "positives": [string, ...],
  "negatives": [string, ...]
}

Be factual and conservative. If the source text does not mention a field, \
use an empty list, empty string, or null rather than inventing details. \
Never fabricate dates, ministry names, or figures."""


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF file's bytes."""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed. Run: pip install pdfplumber")
    text_chunks = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def fetch_url_text(url: str, timeout: int = 30) -> str:
    """
    Fetch a URL and return extracted text.
    Handles both direct PDF links and HTML bill-listing pages.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    is_pdf = "pdf" in content_type.lower() or url.lower().split("?")[0].endswith(".pdf")

    if is_pdf:
        return extract_text_from_pdf_bytes(resp.content)

    # Otherwise treat as HTML
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is not installed. Run: pip install beautifulsoup4")
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def truncate_for_model(text: str, max_chars: int = 60000) -> str:
    """
    Bill PDFs can be long. Keep the beginning (title/preamble/objects &
    reasons -- usually the most information-dense part) and the end
    (often has schedules / amendment details), trimming the middle if needed.
    """
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3):]
    return head + "\n\n...[truncated for length]...\n\n" + tail


# ---------------------------------------------------------------------------
# LLM analysis
# ---------------------------------------------------------------------------

def analyze_bill_text(bill_text: str, api_key: str) -> dict:
    """
    Send bill text to Claude and parse the structured JSON response.
    Raises on API errors; caller should catch and fall back gracefully.
    """
    if anthropic is None:
        raise RuntimeError("anthropic package is not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    bill_text = truncate_for_model(bill_text)

    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"BILL TEXT:\n\n{bill_text}"}],
    )

    raw = "".join(block.text for block in message.content if block.type == "text")
    cleaned = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Offline demo data (used when no API key is supplied, or as a fallback)
# ---------------------------------------------------------------------------

DEMO_BILLS = {
    "Registration of Births and Deaths (Amendment) Bill, 2026": {
        "title": "The Registration of Births and Deaths (Amendment) Bill, 2026",
        "ministry": "Ministry of Home Affairs",
        "introduced_in": "Lok Sabha",
        "introduction_date": "2026-07-29",
        "passed_lok_sabha_date": "2026-07-31",
        "passed_rajya_sabha_date": None,
        "objective": (
            "To tighten the procedure for late registration of births and deaths "
            "under the Registration of Births and Deaths Act, 1969, by introducing "
            "a two-tier approval system based on delay length, and to align "
            "terminology with the Bharatiya Nagarik Suraksha Sanhita, 2023."
        ),
        "key_provisions": [
            "Amends Section 13(3): registrations delayed 1-2 years still need approval from a District/Sub-Divisional/Executive Magistrate after verification and a fee.",
            "Inserts new Section 13(3A): registrations delayed beyond 2 years now require an order from a Judicial Magistrate First Class (JMFC).",
            "Replaces references to CrPC, 1973 with BNSS, 2023, updating the definition of 'Executive Magistrate.'",
        ],
        "related_previous_acts": [
            "Registration of Births and Deaths Act, 1969",
            "Registration of Births and Deaths (Amendment) Act, 2023",
            "Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023",
        ],
        "stakeholders": [
            "General public needing delayed certificates",
            "District/Sub-Divisional/Executive Magistrates",
            "Judicial Magistrates First Class",
            "Registrar General of India and state Registrars",
        ],
        "affected_industries": [
            "Public administration / civil registration",
            "Legal services",
            "Insurance and banking (identity verification)",
        ],
        "risks_and_opportunities": {
            "risks": [
                "Court route for 2+ year delays adds time, cost, and possible legal representation burden.",
                "Judicial magistrates already face heavy caseloads; new case category could add backlog.",
                "Passed without debate, limiting public scrutiny of implementation details.",
            ],
            "opportunities": [
                "Curbs fraudulent or fabricated birth/death certificates.",
                "Improves reliability of vital statistics for welfare targeting and planning.",
                "Aligns legal terminology across statutes.",
            ],
        },
        "citizen_summary": (
            "If you need to register a birth or death that happened a long time ago, "
            "this Bill changes who approves it. For delays of 1-2 years, nothing "
            "changes -- your local magistrate can still approve it. For delays "
            "beyond 2 years, you'll now need to go to a Judicial Magistrate First "
            "Class -- a court official -- instead of a district officer. This is "
            "meant to catch fake certificates, but means more paperwork and time "
            "for people fixing very old records. The Bill also updates legal "
            "references to match India's newer criminal procedure law."
        ),
        "sector_impact": [
            {"sector": "Public administration", "impact": "Procedural change in approval authority for delayed cases", "direction": "Mixed"},
            {"sector": "Judiciary / legal services", "impact": "New case category routed to JMFC courts", "direction": "Mixed"},
            {"sector": "Insurance & banking", "impact": "Better long-run identity data reliability", "direction": "Positive"},
            {"sector": "Ordinary citizens (rural/elderly)", "impact": "Harder, slower path for very old delayed registrations", "direction": "Negative"},
        ],
        "chronology": [
            {"date": "1969", "event": "Registration of Births & Deaths Act enacted"},
            {"date": "2023", "event": "RBD (Amendment) Act: digital Civil Registration System introduced"},
            {"date": "2023", "event": "BNSS replaces CrPC, 1973"},
            {"date": "2026-07-20", "event": "Union Cabinet approves this Bill"},
            {"date": "2026-07-29", "event": "Bill introduced in Lok Sabha"},
            {"date": "2026-07-31", "event": "Passed by Lok Sabha (voice vote, no debate)"},
        ],
        "impact_forecast": {
            "short_term": "Administrative confusion likely as magistrates/registrars/applicants adjust; some backlog as 2+ year cases move to courts.",
            "medium_term": "Judicial magistrates absorb new casework; registration data quality likely improves.",
            "long_term": "More trustworthy vital statistics for welfare delivery, census, and legal identity; possible permanent added judicial caseload.",
        },
        "positives": [
            "Reduces fraudulent/fabricated certificates",
            "Strengthens Civil Registration System credibility",
            "Harmonises legal terminology with BNSS, 2023",
        ],
        "negatives": [
            "Adds a court step for very old delayed registrations",
            "Passed without debate -- limited public scrutiny",
            "Could burden citizens with fewer resources to navigate courts",
        ],
    },
    "Taxation and Other Laws (Amendment) Bill, 2026": {
        "title": "The Taxation and Other Laws (Amendment) Bill, 2026",
        "ministry": "Ministry of Finance",
        "introduced_in": "Lok Sabha",
        "introduction_date": "2026-08-04",
        "passed_lok_sabha_date": "2026-08-06",
        "passed_rajya_sabha_date": "2026-08-10",
        "objective": (
            "To replace the Income-tax (Amendment) Ordinance, 2026 with a "
            "Parliament-enacted law, amending the Income-tax Act, 2025, the "
            "Finance Act, 2026, and the Payment and Settlement Systems Act, "
            "2007, to attract foreign investment and support electronics and "
            "diamond manufacturing."
        ),
        "key_provisions": [
            "Exempts FIIs and the Bank for International Settlements from tax on interest/capital gains from government securities.",
            "15-year tax exemption for specified foreign rough-diamond sellers through notified special zones.",
            "10-year extension of tax exemption for foreign electronics-component suppliers; new exemption for bonded-warehouse storage.",
            "Relaxes eligibility conditions for offshore-registered, India-managed investment funds.",
            "Removes a dividend-exemption restriction for REIT/InvIT unit holders, while raising the SPV surcharge from 10% to 25%.",
            "Amends the Payment and Settlement Systems Act, 2007, affecting the zero-MDR digital payments framework.",
        ],
        "related_previous_acts": [
            "Income-tax (Amendment) Ordinance, 2026",
            "Income-tax Act, 2025",
            "Finance Act, 2026",
            "Payment and Settlement Systems Act, 2007",
        ],
        "stakeholders": [
            "Foreign Institutional Investors and the Bank for International Settlements",
            "Diamond mining, trading, and sightholder companies",
            "Electronics contract manufacturers and foreign suppliers",
            "Offshore investment fund managers",
            "REIT/InvIT unit holders and SPVs",
            "UPI/digital payments ecosystem",
        ],
        "affected_industries": [
            "Financial markets / foreign portfolio investment",
            "Electronics manufacturing",
            "Diamond mining and trading",
            "REITs and InvITs",
            "Digital payments / fintech",
        ],
        "risks_and_opportunities": {
            "risks": [
                "Long-duration exemptions (to FY2041) reduce near-term revenue and lock in policy for 15 years.",
                "Raising SPV surcharge to 25% could raise costs for some REIT/InvIT structures.",
                "Complex multi-Act amendments with limited debate could see interpretation disputes.",
            ],
            "opportunities": [
                "Makes government securities more attractive to foreign capital.",
                "Could draw global electronics/diamond investment into India.",
                "Eases conditions for India-managed offshore funds.",
            ],
        },
        "citizen_summary": (
            "This Bill mostly changes tax rules for large investors and specific "
            "industries, not everyday income tax. It replaces a temporary "
            "government order from June 2026 with a proper law. Foreign "
            "investors in Indian government bonds, and an institution called the "
            "Bank for International Settlements, won't pay tax on interest or "
            "profits from those bonds. Diamond traders and electronics component "
            "suppliers get long tax breaks -- up to 15 years -- to encourage "
            "business in India. There are also technical changes to investment "
            "fund rules, property trust taxation, and digital payments law. For "
            "most ordinary taxpayers, personal income tax doesn't change -- the "
            "effects are mainly on investment flows and specific sectors."
        ),
        "sector_impact": [
            {"sector": "Financial markets / foreign investment", "impact": "Tax exemptions attract foreign capital to G-Secs and fund management", "direction": "Positive"},
            {"sector": "Electronics manufacturing", "impact": "Extended tax exemptions for foreign suppliers/component storage", "direction": "Positive"},
            {"sector": "Diamond trading & mining", "impact": "15-year exemption for specified foreign sellers", "direction": "Positive"},
            {"sector": "REITs / InvITs", "impact": "Eased dividend rules, but higher SPV surcharge", "direction": "Mixed"},
            {"sector": "Digital payments / small merchants", "impact": "Possible changes to zero-MDR framework", "direction": "Neutral"},
        ],
        "chronology": [
            {"date": "2007", "event": "Payment and Settlement Systems Act enacted"},
            {"date": "2025", "event": "Income-tax Act, 2025 enacted"},
            {"date": "2026", "event": "Finance Act, 2026 enacted"},
            {"date": "2026-06-05", "event": "Income-tax (Amendment) Ordinance, 2026 promulgated"},
            {"date": "2026-08-04", "event": "Bill introduced in Lok Sabha"},
            {"date": "2026-08-06", "event": "Passed by Lok Sabha"},
            {"date": "2026-08-10", "event": "Passed by Rajya Sabha"},
            {"date": "2026-08-13", "event": "Reported to have received Presidential assent"},
        ],
        "impact_forecast": {
            "short_term": "Foreign investors and eligible companies begin claiming exemptions; modestly increased FII interest in government bonds.",
            "medium_term": "Electronics/diamond investment decisions factor in the extended exemption horizon; REIT/InvIT structuring may shift.",
            "long_term": "Exemptions run through FY2041, shaping investment and manufacturing decisions over a decade-plus -- a long-term bet on foregone revenue for foreign capital and manufacturing capacity.",
        },
        "positives": [
            "Long-horizon tax certainty for foreign investors and target industries",
            "Could deepen India's government bond market and fund-management ecosystem",
            "Simplifies conditions for offshore-registered, India-managed funds",
        ],
        "negatives": [
            "Reduces near-term tax revenue and constrains future fiscal flexibility",
            "Passed with limited discussion for a bill spanning four Acts",
            "Mixed impact for REIT/InvIT structures",
            "Effects on UPI/digital payments pricing not yet fully clear",
        ],
    },
}


def get_demo_bill(name: str) -> dict:
    return DEMO_BILLS[name]
