# config.py
# Keyword classification rules and project-level constants

FINDING_CATEGORIES = {
    "Protocol Deviation": [
        "protocol deviation", "deviation", "eligibility criteria", "inclusion criteria",
        "exclusion criteria", "visit window", "missed visit", "procedure not followed",
        "unapproved procedure", "dosing error", "dose modification", "off-protocol"
    ],
    "Informed Consent": [
        "informed consent", "consent form", "re-consent", "icf", "consent not obtained",
        "consent expired", "consent version", "unsigned consent", "consent process"
    ],
    "Data Entry / eCRF": [
        "data entry", "ecrf", "crf", "query", "data discrepancy", "missing data",
        "transcription error", "source data", "data clarification", "source document"
    ],
    "Adverse Event Reporting": [
        "adverse event", "ae", "sae", "serious adverse event", "reportable event",
        "safety reporting", "expedited report", "regulatory reporting", "ae not reported"
    ],
    "Investigational Product": [
        "investigational product", "ip", "drug accountability", "temperature excursion",
        "storage condition", "dispensing", "ip log", "study drug", "blind broken",
        "unblinding", "ip destruction", "expired ip"
    ],
    "Regulatory / Essential Documents": [
        "regulatory binder", "essential documents", "irb approval", "irb expiration",
        "financial disclosure", "1572", "cv", "training record", "delegation log",
        "site staff", "credentials", "license"
    ],
    "Facility / Equipment": [
        "equipment calibration", "centrifuge", "freezer", "temperature log",
        "lab certification", "specimen handling", "facility", "lab manual"
    ],
}

SEVERITY_KEYWORDS = {
    "Critical": ["critical", "immediate action", "halt", "stop", "suspension", "fda", "regulatory action"],
    "Major": ["major", "significant", "systemic", "repeated", "recurring", "unresolved", "escalat"],
    "Minor": ["minor", "observation", "recommend", "coaching", "noted", "low risk", "administrative"],
}

FINDING_STATUS_KEYWORDS = {
    "Open": ["open", "pending", "unresolved", "not yet", "outstanding", "action required"],
    "Closed": ["closed", "resolved", "corrected", "completed", "verified", "no further action"],
    "In Progress": ["in progress", "ongoing", "capa in progress", "under review", "being addressed"],
}

OUTPUT_COLUMNS = [
    "report_id",
    "site_id",
    "sponsor",
    "protocol_number",
    "visit_date",
    "monitor_name",
    "finding_id",
    "finding_text",
    "category",
    "severity",
    "status",
    "classification_method",  # "keyword" or "llm"
]
