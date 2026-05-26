"""
etl_pipeline.py
Clinical Monitoring ETL Pipeline
  Extract  → parse findings from Site Visit Report PDFs
  Transform → classify findings (keyword rules, with LLM fallback via Anthropic API)
  Load     → write structured CSVs to data/processed/

Usage:
    python etl_pipeline.py

Environment variable required for LLM fallback:
    ANTHROPIC_API_KEY=<your key>

If ANTHROPIC_API_KEY is not set, unclassified findings are labelled "Unclassified"
instead of calling the API.
"""

import os
import re
import csv
import json
import pdfplumber
import anthropic

from config import FINDING_CATEGORIES, SEVERITY_KEYWORDS, FINDING_STATUS_KEYWORDS, OUTPUT_COLUMNS

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")

# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def parse_header_fields(text: str) -> dict:
    """
    Extract structured header fields from the SVR cover section.
    Handles two-column table layout where fields appear on the same line.
    """
    def find_inline(label: str) -> str:
        """Match 'Label: Value' — value ends at next label or newline."""
        pattern = rf"{re.escape(label)}:\s*([^\n|]+?)(?=\s{{2,}}|\w[\w\s]+:|\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # Report ID is on the same line as Visit Type; grab just the ID token
    rid_match = re.search(r"Report ID:\s*(SVR-[\w\-]+)", text, re.IGNORECASE)
    report_id = rid_match.group(1).strip() if rid_match else ""

    # Sponsor comes from the subtitle line "Clinical Monitoring — <Sponsor>"
    sponsor_match = re.search(r"Clinical Monitoring\s*[—\-]\s*(.+)", text)
    sponsor = sponsor_match.group(1).strip() if sponsor_match else ""

    # Targeted patterns for fields that live in two-column table rows
    sid_match = re.search(r"Site ID:\s*(SITE-\w+)", text, re.IGNORECASE)
    site_id = sid_match.group(1).strip() if sid_match else find_inline("Site ID")

    vd_match = re.search(r"Visit Date:\s*([A-Za-z]+ \d{1,2},\s*\d{4})", text)
    visit_date = vd_match.group(1).strip() if vd_match else find_inline("Visit Date")

    return {
        "report_id": report_id,
        "site_id": site_id,
        "sponsor": sponsor,
        "protocol_number": find_inline("Protocol"),
        "visit_date": visit_date,
        "monitor_name": find_inline("Monitor"),
    }


def split_into_findings(text: str) -> list[dict]:
    """
    Split the 'Findings Detail' section into individual finding dicts.
    Captures severity and status directly from the 'Finding N of M | Sev | Status: X' marker line.
    Returns a list of dicts with keys: text, severity, status.
    """
    findings_match = re.search(
        r"3\.\s*Findings Detail(.*?)(?:4\.\s*Required Actions|$)",
        text, re.DOTALL | re.IGNORECASE
    )
    if not findings_match:
        return []

    section = findings_match.group(1)

    # Match each finding block: marker line + body text
    pattern = re.compile(
        r"Finding\s+\d+\s+of\s+\d+\s*\|?\s*(Critical|Major|Minor)\s*\|?\s*Status:\s*(Open|Closed|In Progress)\s*\n(.*?)(?=Finding\s+\d+\s+of\s+\d+|$)",
        re.DOTALL | re.IGNORECASE
    )

    findings = []
    for match in pattern.finditer(section):
        severity = match.group(1).strip().capitalize()
        status = match.group(2).strip().title()
        body = match.group(3).strip().replace("\n", " ")
        if len(body) > 30:
            findings.append({"text": body, "severity": severity, "status": status})
    return findings


# ── Classification ─────────────────────────────────────────────────────────────

def keyword_classify(finding_text: str, rule_dict: dict) -> str | None:
    """
    Match finding text against keyword rule sets.
    Returns the first matching category name, or None if no match.
    """
    lower = finding_text.lower()
    for category, keywords in rule_dict.items():
        if any(kw in lower for kw in keywords):
            return category
    return None


def keyword_severity(finding_text: str) -> str:
    lower = finding_text.lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return severity
    return "Minor"  # safe default


def keyword_status(finding_text: str) -> str:
    lower = finding_text.lower()
    for status, keywords in FINDING_STATUS_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return status
    return "Open"  # safe default


def llm_classify(finding_text: str, client: anthropic.Anthropic) -> dict:
    """
    Call the Anthropic API to classify a finding that keyword rules couldn't resolve.
    Returns a dict with keys: category, severity, status.
    """
    categories = list(FINDING_CATEGORIES.keys())
    severities = list(SEVERITY_KEYWORDS.keys())
    statuses = list(FINDING_STATUS_KEYWORDS.keys())

    prompt = f"""You are a clinical trial data analyst. Classify the following site monitoring finding.

FINDING TEXT:
{finding_text}

Return ONLY a JSON object with these exact keys and allowed values:
  "category": one of {categories}
  "severity": one of {severities}
  "status": one of {statuses}

No explanation, no markdown fences, just the raw JSON object."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        result = json.loads(raw)
        # Validate values
        result["category"] = result.get("category", "Unclassified")
        result["severity"] = result.get("severity", "Minor")
        result["status"] = result.get("status", "Open")
        return result
    except json.JSONDecodeError:
        return {"category": "Unclassified", "severity": "Minor", "status": "Open"}


def classify_finding(finding_text: str, pdf_severity: str, pdf_status: str,
                     client) -> dict:
    """
    Two-stage classification:
    1. Try keyword rules for category.
    2. If category is ambiguous (None), fall back to LLM.
    Severity and status come directly from the PDF marker line.
    """
    category = keyword_classify(finding_text, FINDING_CATEGORIES)

    if category is not None:
        return {
            "category": category,
            "severity": pdf_severity,
            "status": pdf_status,
            "classification_method": "keyword",
        }

    # LLM fallback for category only
    if client is not None:
        print("    → Keyword rules inconclusive, calling LLM for category...")
        llm_result = llm_classify(finding_text, client)
        return {
            "category": llm_result["category"],
            "severity": pdf_severity,
            "status": pdf_status,
            "classification_method": "llm",
        }

    return {
        "category": "Unclassified",
        "severity": pdf_severity,
        "status": pdf_status,
        "classification_method": "keyword",
    }


# ── ETL orchestration ──────────────────────────────────────────────────────────

def process_pdf(pdf_path: str, client) -> list[dict]:
    """Full extract + transform for a single PDF. Returns a list of row dicts."""
    print(f"  Processing: {os.path.basename(pdf_path)}")
    text = extract_text_from_pdf(pdf_path)
    header = parse_header_fields(text)
    findings = split_into_findings(text)

    rows = []
    for i, finding in enumerate(findings, 1):
        classification = classify_finding(
            finding["text"], finding["severity"], finding["status"], client
        )
        row = {
            **header,
            "finding_id": f"{header.get('report_id', 'UNK')}-F{i:02d}",
            "finding_text": finding["text"],
            **classification,
        }
        rows.append(row)
        method_label = f"[{classification['classification_method'].upper()}]"
        print(f"    Finding {i}: {classification['category']} | "
              f"{classification['severity']} | {classification['status']} {method_label}")
    return rows


def write_csvs(all_rows: list[dict]):
    """Write the full findings table and a summary rollup CSV."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # ── Full findings CSV ──
    findings_path = os.path.join(PROCESSED_DIR, "findings.csv")
    with open(findings_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({col: row.get(col, "") for col in OUTPUT_COLUMNS})
    print(f"\n  Saved: {findings_path}  ({len(all_rows)} findings)")

    # ── Summary rollup CSV ──
    from collections import defaultdict
    summary: dict[str, dict] = defaultdict(lambda: {
        "report_id": "", "site_id": "", "visit_date": "",
        "total_findings": 0, "critical": 0, "major": 0, "minor": 0,
        "open": 0, "in_progress": 0, "closed": 0,
        "keyword_classified": 0, "llm_classified": 0,
    })
    for row in all_rows:
        rid = row.get("report_id", "")
        s = summary[rid]
        s["report_id"] = rid
        s["site_id"] = row.get("site_id", "")
        s["visit_date"] = row.get("visit_date", "")
        s["total_findings"] += 1
        sev = row.get("severity", "").lower()
        if sev == "critical":
            s["critical"] += 1
        elif sev == "major":
            s["major"] += 1
        elif sev == "minor":
            s["minor"] += 1
        stat = row.get("status", "").lower().replace(" ", "_")
        if stat in ("open", "in_progress", "closed"):
            s[stat] += 1
        method = row.get("classification_method", "keyword")
        if method == "llm":
            s["llm_classified"] += 1
        else:
            s["keyword_classified"] += 1

    summary_cols = [
        "report_id", "site_id", "visit_date", "total_findings",
        "critical", "major", "minor", "open", "in_progress", "closed",
        "keyword_classified", "llm_classified",
    ]
    summary_path = os.path.join(PROCESSED_DIR, "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_cols)
        writer.writeheader()
        for s in summary.values():
            writer.writerow(s)
    print(f"  Saved: {summary_path}  ({len(summary)} reports)")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key) if api_key else None
    if client:
        print("Anthropic API key found — LLM fallback enabled.")
    else:
        print("No ANTHROPIC_API_KEY found — running keyword-only mode.")

    pdf_files = sorted(
        [f for f in os.listdir(RAW_DIR) if f.endswith(".pdf")],
    )
    if not pdf_files:
        print(f"No PDFs found in {RAW_DIR}. Run generate_pdfs.py first.")
        return

    print(f"\nFound {len(pdf_files)} PDFs. Starting ETL...\n")
    all_rows = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(RAW_DIR, pdf_file)
        rows = process_pdf(pdf_path, client)
        all_rows.extend(rows)

    print(f"\nTotal findings extracted: {len(all_rows)}")
    write_csvs(all_rows)
    print("\nETL complete.")


if __name__ == "__main__":
    main()
