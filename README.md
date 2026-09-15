# 🏛️ Bill Simplifier

An AI-powered Streamlit application that simplifies Government Bills into easy-to-understand, citizen-friendly insights.

The application allows users to upload a Bill PDF, provide a Bill URL, or explore built-in demo Bills. It extracts the Bill content and uses Anthropic Claude to generate a structured analysis covering the Bill's objective, key provisions, stakeholders, affected industries, risks, opportunities, chronology, and potential impact.

---

## 🚀 Features

- 📄 Upload Government Bill PDFs
- 🔗 Analyze Bills using a PDF or webpage URL
- 🤖 AI-powered Bill analysis using Anthropic Claude
- 📝 Citizen-friendly AI summary
- 🎯 Bill objective and key provisions
- 🕒 Interactive Bill timeline and chronology
- 🏭 Industry and sector impact analysis
- 👥 Stakeholder identification
- ⚠️ Risks and opportunities
- 📈 Short-term, medium-term, and long-term impact forecast
- 📋 Full structured JSON output
- 📥 Download analysis as PDF
- 📥 Download structured analysis as JSON
- 🧪 Built-in demo Bills for testing without an API key

---

## 🖥️ Application Overview

The dashboard is divided into multiple sections:

### 📝 AI Summary

Provides a simplified explanation of the Bill for ordinary citizens.

It includes:

- What the Bill means
- Objective
- Positive aspects
- Negative aspects
- Impact forecast

### 🕒 Timeline

Displays the historical chronology of the Bill, including important events such as:

- Introduction
- Parliamentary approval
- Previous Acts
- Amendments
- Other relevant legislative events

### 🏭 Industry Impact

Analyzes how the Bill may affect different sectors and industries.

The application visualizes the impact using four categories:

- Positive
- Negative
- Mixed
- Neutral

### 📋 Full Details

Displays:

- Key provisions
- Complete structured AI output
- Raw JSON analysis

### ⬇️ Download

Users can download:

- PDF summary report
- Structured JSON analysis

---

## 🔄 Application Workflow

```text
User Input
    │
    ├── Upload Bill PDF
    │
    ├── Paste Bill URL
    │
    └── Select Demo Bill
            │
            ▼
     Extract Bill Text
            │
            ▼
     Text Processing
            │
            ▼
   Anthropic Claude AI
            │
            ▼
   Structured JSON Analysis
            │
            ▼
      Streamlit Dashboard
            │
      ┌─────┼─────────────┐
      ▼     ▼             ▼
   Summary Timeline   Industry Impact
      │     │             │
      └─────┼─────────────┘
            ▼
       Full Details
            │
            ▼
    PDF / JSON Download
````

---

## 🧠 AI Analysis

The application uses Anthropic Claude to convert raw legislative text into a structured JSON format.

The AI analysis covers:

* Bill title
* Ministry
* Introduction details
* Parliamentary status
* Objective
* Key provisions
* Previous Acts and amendments
* Stakeholders
* Affected industries
* Risks
* Opportunities
* Citizen summary
* Sector impact
* Chronology
* Impact forecast
* Positives and negatives

The AI is instructed to provide factual and conservative analysis and avoid fabricating information when details are not available in the source document.

---

## 🛠️ Technologies Used

### Programming Language

* Python

### Framework

* Streamlit

### AI / LLM

* Anthropic Claude

### Data Processing

* Pandas

### PDF Processing

* pdfplumber

### Web Scraping / HTML Processing

* Requests
* BeautifulSoup4

### Data Visualization

* Plotly

### Report Generation

* PDF export functionality

---

## 📁 Project Structure

```text
bill-simplifier/
│
├── app-1.py
├── bill_analyzer.py
├── pdf_export.py
├── requirements.txt
└── README.md
```

### File Description

| File               | Description                                         |
| ------------------ | --------------------------------------------------- |
| `app-1.py`         | Main Streamlit dashboard and user interface         |
| `bill_analyzer.py` | PDF/URL text extraction, AI analysis, and demo data |
| `pdf_export.py`    | Generates downloadable PDF reports                  |
| `requirements.txt` | Python dependencies                                 |
| `README.md`        | Project documentation                               |

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/bill-simplifier.git
```

### 2. Navigate to the project directory

```bash
cd bill-simplifier
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

#### Windows

```bash
venv\Scripts\activate
```

#### macOS / Linux

```bash
source venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` file yet, the main dependencies used by the project include:

```bash
pip install streamlit pandas plotly requests pdfplumber beautifulsoup4 anthropic
```

---

## 🔑 Anthropic API Key

The application uses an Anthropic API key to analyze new Bills with AI.

You can enter the API key directly through the sidebar of the Streamlit application.

```text
Anthropic API Key
```

The application also contains demo Bills that can be explored without an API key.

**Important:** Never upload or commit your actual API key to GitHub.

---

## ▶️ Running the Application

Run the following command from the project directory:

```bash
streamlit run app-1.py
```

The application will open in your browser.

---

## 📄 Input Options

### Option 1 — Demo Bill

Select:

```text
Try a demo bill
```

This allows the application to be explored using the built-in sample Bills without requiring an API key.

### Option 2 — Upload PDF

Select:

```text
Upload PDF
```

and upload a Government Bill PDF.

The application extracts text from the document before sending it for AI analysis.

### Option 3 — Paste URL

Select:

```text
Paste URL
```

and provide a Bill PDF URL or webpage containing the Bill.

The application determines whether the URL points to a PDF or an HTML webpage and extracts the relevant text.

---

## 📊 Example Analysis Output

For each Bill, the application can generate information such as:

```text
Bill Title
Ministry
Introduction Date
Parliamentary Status

Objective
Key Provisions
Citizen Summary

Stakeholders
Affected Industries

Risks
Opportunities

Industry Impact
Bill Chronology

Short-Term Impact
Medium-Term Impact
Long-Term Impact
```

---

## 🧪 Demo Data

The project includes offline sample data for two Bills:

1. Registration of Births and Deaths (Amendment) Bill, 2026
2. Taxation and Other Laws (Amendment) Bill, 2026

This allows the dashboard to be tested and demonstrated without requiring an external API connection.

---

## 📥 Export Options

The application provides two export options.

### PDF Report

Users can download a formatted PDF containing the Bill analysis.

### JSON

Users can download the complete structured AI analysis as a JSON file.

Example:

```json
{
  "title": "Bill Title",
  "ministry": "Ministry Name",
  "objective": "Bill objective",
  "key_provisions": [],
  "stakeholders": [],
  "affected_industries": []
}
```

---

## ⚠️ Limitations

* AI-generated analysis depends on the quality and completeness of the source Bill.
* Very large Bills may be truncated before being sent to the AI model.
* Scanned/image-based PDFs may not provide extractable text.
* Some Government websites may block automated requests.
* AI output should be treated as an explanatory aid and not as legal advice.
* Legislative information should be verified against official Government and Parliamentary sources before making legal or policy decisions.

---

## 🔒 Privacy & Security

* Do not enter confidential or sensitive documents unless you understand where the document content is being sent for processing.
* Never store API keys directly inside the source code.
* Never commit API keys, passwords, or other secrets to GitHub.

---

## 💡 Future Enhancements

Potential improvements include:

* 🔍 Bill comparison between different versions
* 📚 Automatic retrieval from official parliamentary websites
* 🗣️ Multilingual Bill summaries
* 💬 Interactive AI question-answering about a Bill
* 📊 More advanced impact visualizations
* 🔎 Searchable database of analyzed Bills
* 📰 Integration with parliamentary updates
* 📱 Mobile-friendly interface
* 🔐 Secure environment-variable based API key management

---

## 🎯 Use Case

Bill Simplifier is designed to make complex legislative documents easier to understand.

Instead of reading a lengthy legal document, users can quickly explore:

> **What does this Bill do?**

> **Who will be affected?**

> **What are the important changes?**

> **Which industries may be impacted?**

> **What could happen in the short, medium, and long term?**

This makes the project useful for citizens, students, researchers, analysts, journalists, and professionals interested in understanding legislation.

---

## 📌 Project Highlights

* Built using **Python and Streamlit**
* Uses **Generative AI / LLM**
* Converts unstructured legislative text into structured information
* Includes interactive data visualization
* Supports PDF and URL-based inputs
* Provides downloadable reports
* Includes offline demo data
* Designed with a citizen-friendly approach

---

## 👨‍💻 How to Use

1. Start the Streamlit application.
2. Select an input source from the sidebar.
3. Upload a Bill PDF, paste a Bill URL, or select a demo Bill.
4. Enter an Anthropic API key if analyzing a new document.
5. Click **Analyze Bill**.
6. Explore the AI Summary, Timeline, Industry Impact, and Full Details tabs.
7. Download the analysis as a PDF or JSON file.

---

## ⭐ Project Objective

The primary objective of this project is to bridge the gap between complex legislative documents and everyday citizens by using AI to transform lengthy Government Bills into structured, readable, and visual insights.
