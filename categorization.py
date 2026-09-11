import re
from typing import Dict, List, Tuple

# Official 7 Target Categories and Keywords
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Network": [
        "vpn",
        "wifi",
        "wi-fi",
        "network",
        "internet",
        "connection",
        "connectivity",
        "router",
        "dns",
        "firewall",
        "ethernet"
    ],
    "Hardware": [
        "laptop",
        "desktop",
        "monitor",
        "keyboard",
        "mouse",
        "battery",
        "screen",
        "hard drive",
        "computer",
        "docking station"
    ],
    "Software": [
        "excel",
        "word",
        "powerpoint",
        "application",
        "software",
        "crash",
        "crashes",
        "installation",
        "install",
        "update",
        "application error"
    ],
    "Email": [
        "email",
        "outlook",
        "mailbox",
        "mail",
        "inbox",
        "outbox",
        "attachment",
        "spam",
        "email server"
    ],
    "Printer": [
        "printer",
        "printing",
        "print",
        "paper jam",
        "print queue",
        "cartridge",
        "toner",
        "scanner"
    ],
    "Security": [
        "phishing",
        "unauthorized",
        "security",
        "suspicious",
        "malware",
        "antivirus",
        "threat",
        "breach",
        "compromised"
    ],
    "Access/Account": [
        "password",
        "login",
        "log in",
        "account",
        "permission",
        "access denied",
        "credentials",
        "locked account",
        "locked",
        "authentication",
        "sign in"
    ]
}

# Category priority weights for tie-breaking high-risk/specific categories
CATEGORY_WEIGHTS: Dict[str, float] = {
    "Security": 1.2,        # High-priority security keywords take precedence
    "Printer": 1.1,         # Very specific domain
    "Network": 1.0,
    "Hardware": 1.0,
    "Software": 1.0,
    "Email": 1.0,
    "Access/Account": 1.0
}

def find_matched_keywords(text: str) -> Dict[str, List[str]]:
    """
    Find matching keywords across categories using case-insensitive phrase/word boundary matching.
    """
    if not text or not isinstance(text, str):
        return {}

    text_lower = text.lower()
    matches: Dict[str, List[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        matched_kws = []
        for kw in keywords:
            # Word boundary matching (works for multi-word phrases and single words)
            pattern = r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)"
            if re.search(pattern, text_lower):
                matched_kws.append(kw)
        if matched_kws:
            matches[category] = matched_kws

    return matches

def categorize(text: str) -> str:
    """
    Automatically classify ticket text into one of the seven categories:
    Network, Hardware, Software, Email, Printer, Security, Access/Account.
    Falls back to 'General' only when 0 keywords match.
    """
    matches = find_matched_keywords(text)
    if not matches:
        return "General"

    # Score categories by keyword count multiplied by category weight
    # Multi-word phrase matches get extra weight
    def compute_category_score(cat: str) -> float:
        kws = matches[cat]
        base_score = sum(1.5 if " " in kw else 1.0 for kw in kws)
        return base_score * CATEGORY_WEIGHTS.get(cat, 1.0)

    best_category = max(matches.keys(), key=compute_category_score)
    return best_category

def format_keyword_name(kw: str) -> str:
    """Format keywords for display (e.g., VPN, Wi-Fi, Outlook)."""
    special_caps = {
        "vpn": "VPN",
        "wifi": "WiFi",
        "wi-fi": "Wi-Fi",
        "dns": "DNS",
        "outlook": "Outlook",
        "excel": "Excel",
        "word": "Word",
        "powerpoint": "PowerPoint"
    }
    return special_caps.get(kw.lower(), kw)

def explain_category(text: str) -> str:
    """
    Return human-readable explanation with matched category and keywords.
    """
    matches = find_matched_keywords(text)
    if not matches:
        return "Category: General\nMatched keywords: none (no category keywords detected)"

    cat = categorize(text)
    matched_kws = matches.get(cat, [])
    
    if matched_kws:
        kws_str = ", ".join(format_keyword_name(k) for k in matched_kws)
        return f"Category: {cat}\nMatched keywords: {kws_str}"
    else:
        return f"Category: {cat}\nMatched keywords: fallback"
