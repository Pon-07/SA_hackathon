from typing import Dict, Any, List, Tuple
from datetime import datetime

def calculate_breach_risk(
    priority: str,
    agent_load: int,
    affected_users: int,
    remaining_hours: float,
    historical_breach_rate: float = 0.15
) -> Dict[str, Any]:
    """
    Predict the probability that a ticket will breach its resolution SLA.
    Returns a dictionary containing risk_percentage, risk_level, raw_score, reasons, and explanation.
    """
    score = 0
    reasons: List[str] = []

    # 1. Priority Risk
    priority_weights = {
        "Critical": 30,
        "High": 20,
        "Medium": 10,
        "Low": 5
    }
    p_score = priority_weights.get(priority, 10)
    score += p_score
    reasons.append(f"{priority} priority (+{p_score})")

    # 2. Agent Load Risk
    load = int(agent_load)
    if load >= 7:
        l_score = 30
        l_label = f"Heavy agent queue: {load} tickets (+30)"
    elif load >= 5:
        l_score = 20
        l_label = f"Elevated agent queue: {load} tickets (+20)"
    elif load >= 3:
        l_score = 10
        l_label = f"Moderate agent queue: {load} tickets (+10)"
    else:
        l_score = 0
        l_label = f"Low agent queue: {load} ticket{'s' if load != 1 else ''} (+0)"
    score += l_score
    reasons.append(l_label)

    # 3. Affected Users Impact
    users = int(affected_users)
    if users >= 50:
        u_score = 20
        u_label = f"High user impact: {users} affected users (+20)"
    elif users >= 10:
        u_score = 10
        u_label = f"Multi-user impact: {users} affected users (+10)"
    elif users >= 5:
        u_score = 5
        u_label = f"Small group impact: {users} affected users (+5)"
    else:
        u_score = 0
        u_label = f"Single user affected: {users} (+0)"
    score += u_score
    reasons.append(u_label)

    # 4. Time Remaining Risk
    if remaining_hours < 0:
        t_score = 40
        overdue_h = abs(remaining_hours)
        t_label = f"SLA already breached! Overdue by {overdue_h:.1f}h (+40)"
    elif remaining_hours <= 1.0:
        t_score = 30
        t_label = f"Critical time window: <= 1.0h remaining ({remaining_hours:.1f}h left) (+30)"
    elif remaining_hours <= 2.0:
        t_score = 20
        t_label = f"Tight time window: <= 2.0h remaining ({remaining_hours:.1f}h left) (+20)"
    elif remaining_hours <= 4.0:
        t_score = 10
        t_label = f"Moderate resolution window: <= 4.0h remaining ({remaining_hours:.1f}h left) (+10)"
    else:
        t_score = 0
        t_label = f"Ample resolution time remaining: {remaining_hours:.1f}h left (+0)"
    score += t_score
    reasons.append(t_label)

    # 5. Historical Baseline Risk Adjustment
    if historical_breach_rate is not None and historical_breach_rate > 0:
        hist_adj = int(round(historical_breach_rate * 10))
        if hist_adj > 0:
            score += hist_adj
            reasons.append(f"Historical category breach baseline ({historical_breach_rate*100:.0f}% rate, +{hist_adj})")

    # 6. Normalization
    if remaining_hours < 0:
        risk_percentage = min(max(score, 85), 100)
    else:
        risk_percentage = min(max(score, 5), 95)

    # 7. Risk Level Mapping
    if risk_percentage >= 80:
        risk_level = "CRITICAL"
    elif risk_percentage >= 60:
        risk_level = "HIGH"
    elif risk_percentage >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    explanation = explain_breach_risk(risk_percentage, risk_level, reasons)

    return {
        "risk_percentage": risk_percentage,
        "risk_level": risk_level,
        "raw_score": score,
        "reasons": reasons,
        "explanation": explanation
    }

def explain_breach_risk(risk_percentage: int, risk_level: str, reasons: List[str]) -> str:
    """
    Format a clear, human-readable explainability string for breach risk.
    """
    reason_bullets = "\n".join(f"- {r}" for r in reasons)
    return (
        f"Breach Risk: {risk_percentage}%\n"
        f"Risk Level: {risk_level}\n\n"
        f"Reasons:\n{reason_bullets}"
    )
