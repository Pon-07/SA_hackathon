from datetime import datetime, timedelta
from typing import Dict, Tuple, Any

# SLA Configuration by Priority Level
SLA_CONFIG: Dict[str, Dict[str, int]] = {
    "Critical": {"response_hours": 1, "resolution_hours": 4},
    "High": {"response_hours": 2, "resolution_hours": 8},
    "Medium": {"response_hours": 4, "resolution_hours": 24},
    "Low": {"response_hours": 24, "resolution_hours": 72},
}

def calculate_sla(created_at: datetime, priority: str) -> Dict[str, Any]:
    """
    Calculate SLA response and resolution deadlines from ticket creation time and priority.
    """
    sla_info = SLA_CONFIG.get(priority, SLA_CONFIG["Medium"])
    response_hours = sla_info["response_hours"]
    resolution_hours = sla_info["resolution_hours"]

    response_deadline = created_at + timedelta(hours=response_hours)
    resolution_deadline = created_at + timedelta(hours=resolution_hours)

    return {
        "response_sla_hours": response_hours,
        "resolution_sla_hours": resolution_hours,
        "response_deadline": response_deadline,
        "resolution_deadline": resolution_deadline,
    }

def get_sla_status(resolution_deadline: datetime, current_time: datetime = None) -> Tuple[str, str, float]:
    """
    Determine current SLA status (ON TRACK, AT RISK, BREACHED) and formatted remaining/overdue time.
    Returns (status_label, formatted_time_string, remaining_hours_float).
    """
    if current_time is None:
        current_time = datetime.now()

    diff_seconds = (resolution_deadline - current_time).total_seconds()
    remaining_hours = diff_seconds / 3600.0

    if current_time > resolution_deadline:
        status = "BREACHED"
        overdue_seconds = int((current_time - resolution_deadline).total_seconds())
        hours = overdue_seconds // 3600
        minutes = (overdue_seconds % 3600) // 60
        time_display = f"Overdue by: {hours}h {minutes}m"
    elif remaining_hours <= 1.0:
        status = "AT RISK"
        rem_sec = max(0, int(diff_seconds))
        hours = rem_sec // 3600
        minutes = (rem_sec % 3600) // 60
        time_display = f"Time remaining: {hours}h {minutes}m"
    else:
        status = "ON TRACK"
        rem_sec = max(0, int(diff_seconds))
        hours = rem_sec // 3600
        minutes = (rem_sec % 3600) // 60
        time_display = f"Time remaining: {hours}h {minutes}m"

    return status, time_display, remaining_hours

def explain_sla(priority: str) -> str:
    """
    Return human-readable explanation of SLA deadline assignment.
    """
    sla_info = SLA_CONFIG.get(priority, SLA_CONFIG["Medium"])
    resp_h = sla_info["response_hours"]
    res_h = sla_info["resolution_hours"]
    resp_label = f"{resp_h} hour" if resp_h == 1 else f"{resp_h} hours"
    res_label = f"{res_h} hour" if res_h == 1 else f"{res_h} hours"
    return f"SLA determined from priority: {priority} → {resp_label} response / {res_label} resolution."
