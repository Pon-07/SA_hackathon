import re
from typing import Dict, List, Tuple

# Keyword sets for Prioritization Engine
STRONG_URGENCY_KEYWORDS: List[str] = [
    "critical",
    "emergency",
    "production down",
    "server down",
    "system down",
    "completely unavailable",
    "completely down",
    "outage",
    "security breach",
    "data breach",
    "unauthorized access",
    "unauthorized",
    "ransomware",
    "compromised",
    "site down"
]

MEDIUM_URGENCY_KEYWORDS: List[str] = [
    "urgent",
    "immediately",
    "asap",
    "high priority",
    "cannot work",
    "blocking",
    "blocked",
    "time sensitive"
]

IMPACT_KEYWORDS: List[str] = [
    "all users",
    "entire company",
    "company-wide",
    "company wide",
    "entire team",
    "everyone",
    "multiple users",
    "production",
    "business critical",
    "all employees",
    "all staff",
    "company system"
]

CATEGORY_IMPACT_SCORES: Dict[str, int] = {
    "Security": 2,
    "Network": 1,
    "Access/Account": 1,
    "Email": 1,
    "Software": 0,
    "Hardware": 0,
    "Printer": 0,
    "General": 0
}

def find_matched_signals(text: str, keyword_list: List[str]) -> List[str]:
    """Find unique matched keywords/phrases using boundary regex."""
    if not text:
        return []
    text_lower = text.lower()
    matched = []
    for kw in keyword_list:
        pattern = r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)"
        if re.search(pattern, text_lower):
            matched.append(kw)
    return matched

def calculate_priority_score(text: str, category: str, affected_users: int = 1) -> Tuple[int, List[str]]:
    """
    Calculate numerical priority score and structured explanation reasons.
    """
    score = 0
    reasons: List[str] = []
    
    # 1. Strong Urgency Signals (+5)
    strong_matches = find_matched_signals(text, STRONG_URGENCY_KEYWORDS)
    if strong_matches:
        score += 5
        matched_str = ", ".join(strong_matches)
        reasons.append(f"Strong urgency signal: {matched_str} (+5)")
        
    # 2. Medium Urgency Signals (+2) (only if no strong urgency or distinct)
    med_matches = find_matched_signals(text, MEDIUM_URGENCY_KEYWORDS)
    if med_matches and not strong_matches:
        score += 2
        matched_str = ", ".join(med_matches)
        reasons.append(f"Medium urgency signal: {matched_str} (+2)")
        
    # 3. Major Impact Signals (+4)
    impact_matches = find_matched_signals(text, IMPACT_KEYWORDS)
    if impact_matches:
        score += 4
        matched_str = ", ".join(impact_matches)
        reasons.append(f"Major impact: {matched_str} (+4)")
        
    # 4. User Impact
    try:
        users_count = int(affected_users)
    except (ValueError, TypeError):
        users_count = 1
        
    if users_count >= 50:
        score += 2
        reasons.append(f"Affected users: {users_count} (>=50 users, +2)")
    elif users_count >= 10:
        score += 1
        reasons.append(f"Affected users: {users_count} (>=10 users, +1)")
    else:
        if not strong_matches and not impact_matches:
            reasons.append(f"Single user affected ({users_count})")
            
    # 5. Category Impact
    cat_impact = CATEGORY_IMPACT_SCORES.get(category, 0)
    if cat_impact > 0:
        score += cat_impact
        reasons.append(f"Category impact: {category} (+{cat_impact})")
    else:
        if not strong_matches and not impact_matches:
            reasons.append(f"Low-impact category ({category})")
            
    # If no major signals were detected, ensure clear explanation
    if not strong_matches and not med_matches:
        reasons.insert(0, "No major urgency detected")
        
    return score, reasons

def prioritize(text: str, category: str, affected_users: int = 1) -> str:
    """
    Determine priority level: Critical, High, Medium, or Low.
    """
    score, _ = calculate_priority_score(text, category, affected_users)
    
    if score >= 7:
        return "Critical"
    elif score >= 5:
        return "High"
    elif score >= 3:
        return "Medium"
    else:
        return "Low"

def explain_priority(text: str, category: str, affected_users: int = 1) -> str:
    """
    Return human-readable explanation of the priority decision.
    """
    score, reasons = calculate_priority_score(text, category, affected_users)
    priority = prioritize(text, category, affected_users)
    
    # Deduplicate while preserving order
    unique_reasons = []
    seen = set()
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)
            
    reason_lines = "\n".join(f"- {r}" for r in unique_reasons)
    return f"Priority: {priority}\nReasons:\n{reason_lines}"
