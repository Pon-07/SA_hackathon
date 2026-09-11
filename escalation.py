from typing import Dict, Any, List, Tuple

def check_escalation(
    priority: str,
    breach_risk: int,
    remaining_hours: float,
    sla_status: str,
    agent_load: int,
    affected_users: int = 1
) -> Dict[str, Any]:
    """
    Evaluate escalation rules based on priority, SLA status, remaining time, breach risk, and agent load.
    Returns escalation_status, escalation_level, escalation_reason, and recommended_action.
    """
    reasons: List[str] = []
    
    # Priority 1: SLA Breached
    if sla_status == "BREACHED" or remaining_hours < 0:
        overdue_h = abs(remaining_hours)
        reasons.append(f"SLA deadline has been breached (Overdue by {overdue_h:.1f}h)")
        if priority in ["Critical", "High"]:
            reasons.append(f"{priority} priority incident")
        if affected_users >= 10:
            reasons.append(f"Affects {affected_users} users")
        return {
            "escalation_status": "ESCALATION REQUIRED",
            "escalation_level": "CRITICAL ESCALATION",
            "reasons": reasons,
            "escalation_reason": "SLA deadline has been breached.",
            "recommended_action": "Immediately notify supervisor and prioritize resolution.",
            "simulated_action": "🚨 [SIMULATION] High-priority supervisor alert dispatched to incident response channel."
        }

    # Priority 2: Critical Priority / Large-scale Outage (100+ users or >=80% risk)
    if breach_risk >= 80 or (priority == "Critical" and affected_users >= 100):
        reasons.append(f"Very high breach risk ({breach_risk}%)")
        reasons.append(f"{priority} priority with {affected_users} affected users")
        reasons.append(f"{remaining_hours:.1f} hours remaining before SLA deadline")
        if agent_load >= 5:
            reasons.append(f"Assigned agent has {agent_load} open tickets")
        return {
            "escalation_status": "ESCALATION REQUIRED",
            "escalation_level": "CRITICAL ESCALATION",
            "reasons": reasons,
            "escalation_reason": f"Very high breach risk ({breach_risk}%) on critical business operation.",
            "recommended_action": "Notify supervisor and prioritize this ticket immediately.",
            "simulated_action": "🚨 [SIMULATION] Critical escalation ticket flagged for supervisor review & resource reallocation."
        }

    # Priority 3: Critical Ticket Near SLA (<= 1 hour remaining)
    if priority == "Critical" and remaining_hours <= 1.0:
        reasons.append(f"Critical priority incident with only {remaining_hours:.1f}h remaining")
        reasons.append(f"Breach risk elevated at {breach_risk}%")
        return {
            "escalation_status": "ESCALATION REQUIRED",
            "escalation_level": "CRITICAL ESCALATION",
            "reasons": reasons,
            "escalation_reason": "Critical priority ticket is within 1 hour of SLA deadline.",
            "recommended_action": "Immediately escalate to supervisor for intervention.",
            "simulated_action": "🚨 [SIMULATION] Supervisor intervention request automatically queued."
        }

    # Priority 4: SLA Close to Expiry (<= 1 hour remaining for any priority)
    if remaining_hours <= 1.0:
        reasons.append(f"SLA close to expiry ({remaining_hours:.1f}h remaining)")
        reasons.append(f"Priority: {priority}")
        return {
            "escalation_status": "WARNING",
            "escalation_level": "WARNING",
            "reasons": reasons,
            "escalation_reason": f"SLA close to expiry with {remaining_hours:.1f} hours remaining.",
            "recommended_action": "Alert assigned agent and monitor closely.",
            "simulated_action": "⚠️ [SIMULATION] SLA warning notification sent to assigned agent."
        }

    # Priority 5: High Breach Risk (60% <= risk < 80%)
    if 60 <= breach_risk < 80:
        reasons.append(f"High breach risk ({breach_risk}%)")
        reasons.append(f"{priority} priority issue")
        reasons.append(f"{remaining_hours:.1f} hours remaining in SLA window")
        if agent_load >= 3:
            reasons.append(f"Assigned agent has {agent_load} active tickets")
        return {
            "escalation_status": "WARNING",
            "escalation_level": "WARNING",
            "reasons": reasons,
            "escalation_reason": f"Elevated breach risk ({breach_risk}%) detected.",
            "recommended_action": "Monitor ticket closely and consider proactive intervention.",
            "simulated_action": "⚠️ [SIMULATION] Ticket tagged with elevated monitoring status."
        }

    # Priority 6: High Agent Queue Load (>= 7 tickets on Critical/High)
    if agent_load >= 7 and priority in ["Critical", "High"]:
        reasons.append(f"Assigned agent has a high workload ({agent_load} open tickets)")
        reasons.append(f"{priority} priority issue requires active bandwidth")
        return {
            "escalation_status": "WARNING",
            "escalation_level": "WARNING",
            "reasons": reasons,
            "escalation_reason": "Assigned agent has a high workload.",
            "recommended_action": "Consider reassigning or adding additional support due to high agent workload.",
            "simulated_action": "⚠️ [SIMULATION] Workload balancing alert triggered for queue supervisor."
        }

    # Priority 7: Normal / No Escalation
    reasons.append("SLA is on track with sufficient remaining time")
    reasons.append(f"Breach risk is low ({breach_risk}%)")
    reasons.append(f"Agent workload is manageable ({agent_load} tickets)")
    return {
        "escalation_status": "NO ESCALATION",
        "escalation_level": "NO ESCALATION",
        "reasons": reasons,
        "escalation_reason": "Ticket is currently on track with healthy SLA buffer.",
        "recommended_action": "No escalation required. Ticket is currently on track.",
        "simulated_action": ""
    }

def explain_escalation(escalation_data: Dict[str, Any]) -> str:
    """Format a clear, human-readable explainability string for escalation decisions."""
    level = escalation_data["escalation_level"]
    status = escalation_data["escalation_status"]
    action = escalation_data["recommended_action"]
    reasons = escalation_data.get("reasons", [escalation_data.get("escalation_reason", "")])
    
    reason_bullets = "\n".join(f"- {r}" for r in reasons)
    
    return (
        f"Status: {status}\n"
        f"Level: {level}\n\n"
        f"Reasons:\n{reason_bullets}\n\n"
        f"Recommended Action:\n{action}"
    )
