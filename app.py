import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import io

# Import Core Pipeline Modules
from categorization import (
    CATEGORY_KEYWORDS,
    categorize,
    explain_category
)
from prioritization import (
    prioritize,
    explain_priority,
    calculate_priority_score
)
from sla import (
    SLA_CONFIG,
    calculate_sla,
    get_sla_status,
    explain_sla
)
from routing import (
    DEFAULT_AGENTS,
    get_initial_agents,
    assign_ticket,
    explain_assignment
)
from risk import (
    calculate_breach_risk,
    explain_breach_risk
)
from retrieval import (
    TicketSimilarityEngine,
    find_similar_ticket
)
from escalation import (
    check_escalation,
    explain_escalation
)

# -------------------------------------------------------------
# App Configuration & Global Modern SaaS Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="Intelligent IT SLA Management",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Typography & Background Adjustments */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Modern Metric container override */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(51, 65, 85, 0.7);
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(8px);
    }
    div[data-testid="metric-container"]:hover {
        border-color: rgba(99, 102, 241, 0.45);
    }
    
    /* Custom KPI Cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.76rem;
        color: #64748b;
        margin-top: 4px;
    }
    .kpi-blue { border-left: 4px solid #3b82f6; }
    .kpi-green { border-left: 4px solid #10b981; }
    .kpi-amber { border-left: 4px solid #f59e0b; }
    .kpi-red { border-left: 4px solid #ef4444; }
    .kpi-purple { border-left: 4px solid #8b5cf6; }
    .kpi-cyan { border-left: 4px solid #06b6d4; }
    
    /* Status & Priority Badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .badge-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-green { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-purple { background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); }
    .badge-cyan { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.4); }
    .badge-slate { background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.4); }
    
    /* Chat Conversation Styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px;
        background: rgba(15, 23, 42, 0.65);
        border-radius: 12px;
        border: 1px solid rgba(51, 65, 85, 0.6);
        margin-bottom: 16px;
        max-height: 440px;
        overflow-y: auto;
    }
    .chat-msg-emp {
        align-self: flex-end;
        max-width: 80%;
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
        color: #ffffff;
        padding: 10px 16px;
        border-radius: 16px 16px 2px 16px;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.25);
        font-size: 0.92rem;
    }
    .chat-msg-agent {
        align-self: flex-start;
        max-width: 80%;
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
        color: #ffffff;
        padding: 10px 16px;
        border-radius: 16px 16px 16px 2px;
        box-shadow: 0 2px 10px rgba(99, 102, 241, 0.25);
        font-size: 0.92rem;
    }
    .chat-msg-sys {
        align-self: center;
        max-width: 90%;
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(71, 85, 105, 0.5);
        color: #cbd5e1;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        text-align: center;
    }
    .chat-meta {
        font-size: 0.72rem;
        opacity: 0.85;
        margin-top: 4px;
        display: block;
    }

    /* AI Decision Trail Card */
    .trail-step {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(51, 65, 85, 0.65);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .trail-num {
        display: inline-block;
        width: 22px;
        height: 22px;
        line-height: 22px;
        text-align: center;
        background: #3b82f6;
        color: white;
        border-radius: 50%;
        font-size: 0.72rem;
        font-weight: 700;
        margin-right: 8px;
    }
    
    /* Role Header Badges */
    .role-badge-emp {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
        letter-spacing: 0.3px;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }
    .role-badge-ops {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
        letter-spacing: 0.3px;
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
    }
    
    /* System Status Widget */
    .sys-status-widget {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 10px;
        padding: 12px 14px;
        font-size: 0.8rem;
        color: #94a3b8;
        line-height: 1.6;
        margin-top: 15px;
    }
    .sys-dot-green {
        color: #10b981;
        font-weight: bold;
        margin-right: 5px;
    }
    
    /* Landing Cards */
    .landing-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 16px;
        padding: 28px 24px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
        height: 100%;
    }
    .landing-card:hover {
        transform: translateY(-3px);
    }
    .landing-card-emp {
        border-top: 4px solid #3b82f6;
    }
    .landing-card-ops {
        border-top: 4px solid #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

DATASET_PATH = Path(__file__).parent / "tickets.csv"

# -------------------------------------------------------------
# Data Loading & Caching (Read-Only)
# -------------------------------------------------------------
@st.cache_data
def load_historical_tickets(filepath: Path) -> pd.DataFrame:
    """Load historical ground-truth ticket dataset without altering records."""
    if not filepath.exists():
        st.error(f"Dataset file not found at: {filepath}")
        return pd.DataFrame()
    return pd.read_csv(filepath)

df_historical = load_historical_tickets(DATASET_PATH)

if df_historical.empty:
    st.error("⚠️ Historical dataset (tickets.csv) is missing or empty.")
    st.stop()

@st.cache_resource
def get_cached_similarity_engine(df: pd.DataFrame) -> TicketSimilarityEngine:
    """Fit and cache TF-IDF similarity engine once."""
    return TicketSimilarityEngine(df)

similarity_engine = get_cached_similarity_engine(df_historical)

historical_breach_rate = (
    float((df_historical["sla_breached"] == True).mean())
    if "sla_breached" in df_historical.columns
    else 0.15
)

# -------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------
if "current_role" not in st.session_state:
    st.session_state["current_role"] = None

if "agent_pool" not in st.session_state:
    st.session_state["agent_pool"] = get_initial_agents()

if "ticket_counter" not in st.session_state:
    st.session_state["ticket_counter"] = 1

if "session_tickets" not in st.session_state:
    st.session_state["session_tickets"] = []

# -------------------------------------------------------------
# UI Badge & Helper Renderers
# -------------------------------------------------------------
def get_priority_badge(priority: str) -> str:
    color_map = {
        "Critical": "badge-red",
        "High": "badge-amber",
        "Medium": "badge-blue",
        "Low": "badge-green"
    }
    css_class = color_map.get(priority, "badge-slate")
    return f'<span class="badge {css_class}">{priority}</span>'

def get_status_badge(status: str) -> str:
    color_map = {
        "Open": "badge-blue",
        "In Progress": "badge-amber",
        "Resolved": "badge-green"
    }
    css_class = color_map.get(status, "badge-slate")
    return f'<span class="badge {css_class}">{status}</span>'

def get_sla_badge(sla_status: str) -> str:
    if "BREACHED" in sla_status or "🔴" in sla_status:
        return '<span class="badge badge-red">BREACHED</span>'
    elif "AT RISK" in sla_status or "🟡" in sla_status:
        return '<span class="badge badge-amber">AT RISK</span>'
    return '<span class="badge badge-green">ON TRACK</span>'

def get_risk_badge(risk_level: str) -> str:
    color_map = {
        "CRITICAL": "badge-red",
        "HIGH": "badge-red",
        "MEDIUM": "badge-amber",
        "LOW": "badge-green"
    }
    css_class = color_map.get(risk_level.upper(), "badge-slate")
    return f'<span class="badge {css_class}">{risk_level} RISK</span>'

def get_escalation_badge(esc_level: str) -> str:
    if "CRITICAL" in esc_level:
        return f'<span class="badge badge-red">{esc_level}</span>'
    elif "REQUIRED" in esc_level or "WARNING" in esc_level:
        return f'<span class="badge badge-amber">{esc_level}</span>'
    return f'<span class="badge badge-green">{esc_level}</span>'

def render_sidebar_status():
    st.markdown("""
    <div class="sys-status-widget">
        <strong style="color: #f1f5f9; letter-spacing: 0.5px; font-size: 0.75rem;">SYSTEM STATUS</strong><br>
        <span class="sys-dot-green">●</span> AI Triage Engine: <span style="color:#34d399;">Online</span><br>
        <span class="sys-dot-green">●</span> SLA Monitoring: <span style="color:#34d399;">Active</span><br>
        <span class="sys-dot-green">●</span> Routing Engine: <span style="color:#34d399;">Online</span><br>
        <span class="sys-dot-green">●</span> Knowledge Base: <span style="color:#60a5fa;">1,000 Tickets</span>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# Helper: End-to-End Automated Pipeline Execution
# -------------------------------------------------------------
def process_new_complaint(subject: str, description: str, affected_users: int = 1) -> dict:
    """
    Execute full 7-stage pipeline for a new complaint:
    1. Categorize
    2. Prioritize
    3. Calculate SLA
    4. Assign Agent
    5. Predict Breach Risk
    6. Retrieve Similar Historical Tickets
    7. Evaluate Escalation
    """
    created_time = datetime.now()
    ticket_text = f"{subject} {description}".strip()
    
    ticket_id = f"NEW-{st.session_state['ticket_counter']:04d}"
    st.session_state["ticket_counter"] += 1
    
    # 1. Categorization
    pred_category = categorize(ticket_text)
    cat_exp = explain_category(ticket_text)
    
    # 2. Prioritization
    pred_priority = prioritize(ticket_text, pred_category, affected_users)
    pri_exp = explain_priority(ticket_text, pred_category, affected_users)
    
    # 3. SLA Deadlines
    sla_info = calculate_sla(created_time, pred_priority)
    sla_status, time_display, remaining_hours = get_sla_status(
        sla_info["resolution_deadline"],
        current_time=created_time
    )
    sla_exp = explain_sla(pred_priority)
    
    # 4. Intelligent Routing
    assignment_info = assign_ticket(pred_category, st.session_state["agent_pool"])
    
    # 5. Breach Risk
    risk_info = calculate_breach_risk(
        priority=pred_priority,
        agent_load=assignment_info["new_load"],
        affected_users=affected_users,
        remaining_hours=remaining_hours,
        historical_breach_rate=historical_breach_rate
    )
    
    # 6. Similar Ticket Retrieval
    similar_records = similarity_engine.find_similar_tickets(
        subject=subject,
        description=description,
        category=pred_category,
        top_n=3,
        threshold=0.15
    )
    sim_exp = similarity_engine.explain_similarity(similar_records, threshold=0.15)
    
    # 7. Escalation Check
    escalation_info = check_escalation(
        priority=pred_priority,
        breach_risk=risk_info["risk_percentage"],
        remaining_hours=remaining_hours,
        sla_status=sla_status,
        agent_load=assignment_info["new_load"],
        affected_users=affected_users
    )
    esc_exp = explain_escalation(escalation_info)
    
    ticket_record = {
        "ticket_id": ticket_id,
        "subject": subject,
        "description": description,
        "affected_users": affected_users,
        "created_at": created_time,
        "category": pred_category,
        "category_explanation": cat_exp,
        "priority": pred_priority,
        "priority_explanation": pri_exp,
        "response_deadline": sla_info["response_deadline"],
        "resolution_deadline": sla_info["resolution_deadline"],
        "response_sla_hours": sla_info["response_sla_hours"],
        "resolution_sla_hours": sla_info["resolution_sla_hours"],
        "sla_status": sla_status,
        "time_display": time_display,
        "sla_explanation": sla_exp,
        "assigned_agent": assignment_info["assigned_agent"],
        "agent_skills": assignment_info["skills"],
        "agent_previous_load": assignment_info["previous_load"],
        "agent_new_load": assignment_info["new_load"],
        "assignment_explanation": assignment_info["explanation"],
        "risk_percentage": risk_info["risk_percentage"],
        "risk_level": risk_info["risk_level"],
        "risk_reasons": risk_info["reasons"],
        "risk_explanation": risk_info["explanation"],
        "similar_records": similar_records,
        "similarity_explanation": sim_exp,
        "escalation_status": escalation_info["escalation_status"],
        "escalation_level": escalation_info["escalation_level"],
        "escalation_reasons": escalation_info["reasons"],
        "escalation_action": escalation_info["recommended_action"],
        "simulated_action": escalation_info["simulated_action"],
        "escalation_explanation": esc_exp,
        "status": "Open",
        "resolved_at": None,
        "resolution_hours": None,
        "sla_result": None,
        "resolution_notes": "",
        "messages": [
            {
                "sender": "System",
                "message": f"Support ticket created. Assigned to {assignment_info['assigned_agent']} with {sla_info['resolution_sla_hours']}h resolution target.",
                "timestamp": created_time
            }
        ]
    }
    
    st.session_state["session_tickets"].insert(0, ticket_record)
    return ticket_record


# -------------------------------------------------------------
# SCREEN 1: LANDING / ROLE SELECTION
# -------------------------------------------------------------
def render_landing_screen():
    st.markdown("""
        <div style="text-align: center; padding: 45px 0 15px 0;">
            <div style="display: inline-block; padding: 6px 16px; background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 20px; color: #60a5fa; font-weight: 600; font-size: 0.85rem; margin-bottom: 12px; letter-spacing: 0.5px;">
                IT SERVICE MANAGEMENT PLATFORM
            </div>
            <h1 style="font-size: 2.9rem; font-weight: 800; margin-bottom: 10px; background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Intelligent IT SLA Management
            </h1>
            <p style="font-size: 1.2rem; color: #94a3b8; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.5;">
                Automated triage, intelligent routing and proactive SLA protection
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("""
            <div class="landing-card landing-card-emp">
                <div style="font-size: 2.2rem; margin-bottom: 10px;">👨‍💻</div>
                <h2 style="color: #60a5fa; margin: 0 0 10px 0; font-size: 1.6rem; font-weight: 700;">EMPLOYEE PORTAL</h2>
                <p style="color: #cbd5e1; font-size: 1.05rem; line-height: 1.5; margin-bottom: 20px;">
                    Submit complaints, track tickets and communicate with IT
                </p>
                <ul style="color: #94a3b8; font-size: 0.92rem; line-height: 1.8; margin-bottom: 25px;">
                    <li>✓ Fast complaint submission with automated triage</li>
                    <li>✓ Real-time SLA countdown and status tracking</li>
                    <li>✓ Ticket-specific support conversation with IT Agent</li>
                    <li>✓ Exportable official complaint reports (.TXT / .CSV)</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("🚀 Enter Employee Portal", use_container_width=True, type="primary"):
            st.session_state["current_role"] = "employee"
            st.rerun()

    with col_right:
        st.markdown("""
            <div class="landing-card landing-card-ops">
                <div style="font-size: 2.2rem; margin-bottom: 10px;">🧑‍💼</div>
                <h2 style="color: #c084fc; margin: 0 0 10px 0; font-size: 1.6rem; font-weight: 700;">IT OPERATIONS CENTER</h2>
                <p style="color: #cbd5e1; font-size: 1.05rem; line-height: 1.5; margin-bottom: 20px;">
                    Monitor tickets, SLAs, risks, workload and escalations
                </p>
                <ul style="color: #94a3b8; font-size: 0.92rem; line-height: 1.8; margin-bottom: 25px;">
                    <li>✓ 7-stage automated incident triage & routing engine</li>
                    <li>✓ Proactive SLA breach prediction & live escalation center</li>
                    <li>✓ Explainable 🧠 AI Decision Trail breakdown</li>
                    <li>✓ Skill-based workload balancing & status workflow manager</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("🛡️ Enter IT Operations Center", use_container_width=True, type="secondary"):
            st.session_state["current_role"] = "agent"
            st.rerun()

    st.write("")
    st.divider()
    
    # System Status Section
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.9rem;'><span style='color:#10b981; font-weight:bold;'>●</span> <strong>AI Triage Engine:</strong> <span style='color:#34d399;'>Online</span></div>", unsafe_allow_html=True)
    with col_s2:
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.9rem;'><span style='color:#10b981; font-weight:bold;'>●</span> <strong>SLA Monitoring:</strong> <span style='color:#34d399;'>Active</span></div>", unsafe_allow_html=True)
    with col_s3:
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.9rem;'><span style='color:#60a5fa; font-weight:bold;'>●</span> <strong>Ticket Intelligence:</strong> <span style='color:#60a5fa;'>Ready (1,000 Tickets)</span></div>", unsafe_allow_html=True)


# -------------------------------------------------------------
# SCREEN 2: EMPLOYEE PORTAL
# -------------------------------------------------------------
def render_employee_dashboard():
    # Sidebar
    with st.sidebar:
        st.markdown("<span class='role-badge-emp'>👨‍💻 Employee Portal</span>", unsafe_allow_html=True)
        st.title("My IT Support")
        st.caption("Intelligent IT SLA Management")
        
        emp_nav = st.radio(
            "Employee Navigation",
            ["🏠 My Dashboard", "➕ New Complaint", "📋 My Complaints", "📄 Complaint Report"],
            label_visibility="collapsed"
        )
        
        st.divider()
        if st.button("🔄 Switch Role", use_container_width=True):
            st.session_state["current_role"] = None
            st.rerun()
            
        render_sidebar_status()

    # Dynamic refresh of SLA status for live session tickets
    now = datetime.now()
    for t in st.session_state["session_tickets"]:
        if t["status"] != "Resolved":
            status, time_disp, rem_h = get_sla_status(t["resolution_deadline"], current_time=now)
            t["sla_status"] = status
            t["time_display"] = time_disp

    session_tickets = st.session_state["session_tickets"]

    # ---------------------------------------------------------
    # VIEW 1: My Dashboard
    # ---------------------------------------------------------
    if emp_nav == "🏠 My Dashboard":
        st.header("🏠 My Dashboard")
        st.caption("Track your submitted technical requests and SLA resolution countdowns.")

        open_count = sum(1 for t in session_tickets if t["status"] == "Open")
        prog_count = sum(1 for t in session_tickets if t["status"] == "In Progress")
        res_count = sum(1 for t in session_tickets if t["status"] == "Resolved")

        # 3 Colorful KPI Cards
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">OPEN</div>
                <div class="kpi-value" style="color:#60a5fa;">{open_count}</div>
                <div class="kpi-sub">Awaiting technician pick-up</div>
            </div>
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">IN PROGRESS</div>
                <div class="kpi-value" style="color:#fbbf24;">{prog_count}</div>
                <div class="kpi-sub">Actively under investigation</div>
            </div>
            <div class="kpi-card kpi-green">
                <div class="kpi-title">RESOLVED</div>
                <div class="kpi-value" style="color:#34d399;">{res_count}</div>
                <div class="kpi-sub">Successfully closed requests</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📋 Recent Complaints")
            if not session_tickets:
                st.info("You haven't submitted any complaints yet. Use **New Complaint** to submit a support request.")
            else:
                table_html = """
                <div style="overflow-x: auto; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border: 1px solid rgba(51, 65, 85, 0.6); padding: 10px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(71, 85, 105, 0.6); color: #94a3b8;">
                                <th style="padding: 10px;">Ticket ID</th>
                                <th style="padding: 10px;">Issue</th>
                                <th style="padding: 10px;">Category</th>
                                <th style="padding: 10px;">Priority</th>
                                <th style="padding: 10px;">Status</th>
                                <th style="padding: 10px;">Agent</th>
                                <th style="padding: 10px;">SLA Status</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for t in session_tickets[:5]:
                    table_html += f"""
                        <tr style="border-bottom: 1px solid rgba(51, 65, 85, 0.4); color: #f1f5f9;">
                            <td style="padding: 10px; font-weight: 600; color: #60a5fa;">{t['ticket_id']}</td>
                            <td style="padding: 10px;">{t['subject']}</td>
                            <td style="padding: 10px;"><span class="badge badge-slate">{t['category']}</span></td>
                            <td style="padding: 10px;">{get_priority_badge(t['priority'])}</td>
                            <td style="padding: 10px;">{get_status_badge(t['status'])}</td>
                            <td style="padding: 10px; color: #cbd5e1;">{t['assigned_agent']}</td>
                            <td style="padding: 10px;">{get_sla_badge(t['sla_status'])}</td>
                        </tr>
                    """
                table_html += "</tbody></table></div>"
                st.markdown(table_html, unsafe_allow_html=True)

        with col_right:
            st.subheader("⚡ Quick Help")
            st.markdown("""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 12px; padding: 18px;">
                <strong style="color: #60a5fa;">Common Support Categories:</strong>
                <ul style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.8; margin-top: 8px; padding-left: 20px;">
                    <li><strong>Network:</strong> Wi-Fi, VPN, Connectivity</li>
                    <li><strong>Software:</strong> Office, Excel, OS Errors</li>
                    <li><strong>Access:</strong> Okta, SSO, Passwords</li>
                    <li><strong>Hardware:</strong> Laptops, Monitors</li>
                    <li><strong>Printer:</strong> Paper Jams, Queues</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VIEW 2: New Complaint (with Demo Mode quick-fill)
    # ---------------------------------------------------------
    elif emp_nav == "➕ New Complaint":
        st.header("➕ Submit New IT Complaint")
        st.caption("Provide issue details. Our automated triage engine will categorize, prioritize, and assign your ticket immediately.")

        # 🎬 Demo Mode Scenarios Section
        st.markdown("##### 🎬 Demo Mode (Quick-Fill Scenarios)")
        st.caption("Click any scenario to pre-fill the form, then submit to test the live triage pipeline:")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            if st.button("🌐 1. VPN Outage", use_container_width=True):
                st.session_state["emp_subj"] = "Production VPN outage"
                st.session_state["emp_desc"] = "The production VPN is completely down and all employees are unable to connect."
                st.session_state["emp_users"] = 100
        with col_p2:
            if st.button("🔒 2. Security Incident", use_container_width=True):
                st.session_state["emp_subj"] = "Phishing email alert"
                st.session_state["emp_desc"] = "Suspicious email with malicious attachment received by multiple finance employees asking for password reset."
                st.session_state["emp_users"] = 25
        with col_p3:
            if st.button("💻 3. Excel Crash", use_container_width=True):
                st.session_state["emp_subj"] = "Excel crash on quarterly report"
                st.session_state["emp_desc"] = "Excel crashes immediately whenever I try to open or save the financial spreadsheet report."
                st.session_state["emp_users"] = 1
        with col_p4:
            if st.button("🖨️ 4. Printer Issue", use_container_width=True):
                st.session_state["emp_subj"] = "3rd floor printer paper jam"
                st.session_state["emp_desc"] = "The 3rd floor Xerox office printer is jammed with a red error light and cannot print documents."
                st.session_state["emp_users"] = 5

        default_s = st.session_state.get("emp_subj", "")
        default_d = st.session_state.get("emp_desc", "")
        default_u = st.session_state.get("emp_users", 1)

        with st.form("employee_complaint_form"):
            new_subject = st.text_input("Issue Title:", value=default_s, placeholder="Brief summary of the issue...")
            col_u1, _ = st.columns([1, 2])
            with col_u1:
                new_users = st.number_input("Affected Users:", min_value=1, value=int(default_u), step=1)
            new_desc = st.text_area("Description:", value=default_d, height=120, placeholder="Describe symptoms, error codes, and what you were trying to do...")
            submit_btn = st.form_submit_button("Submit Complaint", type="primary", use_container_width=True)

        if submit_btn:
            if not new_subject.strip() or not new_desc.strip():
                st.error("Please provide both an Issue Title and Description for your complaint.")
            else:
                record = process_new_complaint(new_subject, new_desc, new_users)
                
                # Reset prefill state
                st.session_state["emp_subj"] = ""
                st.session_state["emp_desc"] = ""
                st.session_state["emp_users"] = 1
                
                st.success("✅ **Complaint submitted successfully!**")
                
                # Post-submission confirmation card
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 12px; padding: 22px; margin-top: 15px;">
                    <h3 style="color: #60a5fa; margin-top: 0;">Ticket Confirmation: <code>{record['ticket_id']}</code></h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 14px; margin: 15px 0;">
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Category:</span><br><strong>{record['category']}</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Priority:</span><br>{get_priority_badge(record['priority'])}</div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Assigned Agent:</span><br><strong>{record['assigned_agent']}</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Response SLA:</span><br><strong>{record['response_sla_hours']} Hours</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Resolution SLA:</span><br><strong>{record['resolution_sla_hours']} Hours</strong></div>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; font-size: 0.9rem; color: #cbd5e1;">
                        ⏱️ <strong>Resolution Deadline:</strong> <code>{record['resolution_deadline'].strftime('%d %b %Y, %I:%M %p')}</code> ({record['sla_status']}) | <strong>Status:</strong> {get_status_badge(record['status'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VIEW 3: My Complaints & Live Chat with IT Agent
    # ---------------------------------------------------------
    elif emp_nav == "📋 My Complaints":
        st.header("📋 My Complaints")
        st.caption("Inspect complaint progress, monitor resolution deadlines, and communicate in real time with your assigned IT technician.")

        if not session_tickets:
            st.info("You haven't submitted any complaints yet. Use **New Complaint** to submit a support request.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                status_filter = st.selectbox("Filter Status:", ["All", "Open", "In Progress", "Resolved"])
            with col_f2:
                pri_filter = st.selectbox("Filter Priority:", ["All", "Critical", "High", "Medium", "Low"])
            with col_f3:
                cat_filter = st.selectbox("Filter Category:", ["All"] + sorted(list(set(t["category"] for t in session_tickets))))

            filtered_list = session_tickets
            if status_filter != "All":
                filtered_list = [t for t in filtered_list if t["status"] == status_filter]
            if pri_filter != "All":
                filtered_list = [t for t in filtered_list if t["priority"] == pri_filter]
            if cat_filter != "All":
                filtered_list = [t for t in filtered_list if t["category"] == cat_filter]

            table_html = """
            <div style="overflow-x: auto; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border: 1px solid rgba(51, 65, 85, 0.6); padding: 10px; margin-bottom: 20px;">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                    <thead>
                        <tr style="border-bottom: 1px solid rgba(71, 85, 105, 0.6); color: #94a3b8;">
                            <th style="padding: 10px;">Ticket ID</th>
                            <th style="padding: 10px;">Issue</th>
                            <th style="padding: 10px;">Category</th>
                            <th style="padding: 10px;">Priority</th>
                            <th style="padding: 10px;">Status</th>
                            <th style="padding: 10px;">Assigned Agent</th>
                            <th style="padding: 10px;">SLA Status</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for t in filtered_list:
                table_html += f"""
                    <tr style="border-bottom: 1px solid rgba(51, 65, 85, 0.4); color: #f1f5f9;">
                        <td style="padding: 10px; font-weight: 600; color: #60a5fa;">{t['ticket_id']}</td>
                        <td style="padding: 10px;">{t['subject']}</td>
                        <td style="padding: 10px;"><span class="badge badge-slate">{t['category']}</span></td>
                        <td style="padding: 10px;">{get_priority_badge(t['priority'])}</td>
                        <td style="padding: 10px;">{get_status_badge(t['status'])}</td>
                        <td style="padding: 10px; color: #cbd5e1;">{t['assigned_agent']}</td>
                        <td style="padding: 10px;">{get_sla_badge(t['sla_status'])}</td>
                    </tr>
                """
            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)

            st.divider()

            # Ticket Details & Chat
            st.subheader("📄 Ticket Details")
            ticket_options = [t["ticket_id"] + " - " + t["subject"] for t in session_tickets]
            selected_ticket_str = st.selectbox("Select Ticket to View Details & Conversation:", ticket_options)
            
            selected_id = selected_ticket_str.split(" - ")[0]
            selected_ticket = next((t for t in session_tickets if t["ticket_id"] == selected_id), None)

            if selected_ticket:
                # Ticket summary card
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.75); border: 1px solid rgba(51, 65, 85, 0.7); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(51, 65, 85, 0.6); padding-bottom: 12px; margin-bottom: 14px;">
                        <div>
                            <span style="font-size: 1.25rem; font-weight: 700; color: #60a5fa;">{selected_ticket['ticket_id']}</span>
                            <span style="margin-left: 10px;">{get_status_badge(selected_ticket['status'])}</span>
                            <span style="margin-left: 6px;">{get_priority_badge(selected_ticket['priority'])}</span>
                        </div>
                        <div>
                            {get_sla_badge(selected_ticket['sla_status'])}
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; font-size: 0.9rem; margin-bottom: 14px;">
                        <div><strong style="color:#94a3b8;">Issue:</strong><br>{selected_ticket['subject']}</div>
                        <div><strong style="color:#94a3b8;">Category:</strong><br>{selected_ticket['category']}</div>
                        <div><strong style="color:#94a3b8;">Assigned Agent:</strong><br>{selected_ticket['assigned_agent']}</div>
                        <div><strong style="color:#94a3b8;">Created Time:</strong><br>{selected_ticket['created_at'].strftime('%d %b %Y, %I:%M %p')}</div>
                        <div><strong style="color:#94a3b8;">SLA Deadline:</strong><br>{selected_ticket['resolution_deadline'].strftime('%d %b %Y, %I:%M %p')}</div>
                        <div><strong style="color:#94a3b8;">Time Remaining:</strong><br>{selected_ticket['time_display']}</div>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 12px; border-radius: 8px; font-size: 0.9rem; color: #cbd5e1;">
                        <strong>Description:</strong> {selected_ticket['description']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if selected_ticket["status"] == "Resolved":
                    st.success(
                        f"✅ **Resolved successfully on:** `{selected_ticket['resolved_at'].strftime('%d %b %Y, %I:%M %p')}` | "
                        f"**Resolution Time:** `{selected_ticket['resolution_hours']:.1f} hrs` | "
                        f"**SLA Result:** `{selected_ticket['sla_result']}`"
                    )

                st.divider()

                # Chat with IT Agent (Modern Chat Interface)
                st.subheader(f"💬 Chat with IT Agent — {selected_ticket['ticket_id']}")
                st.caption("Communicate directly with your assigned technician in real time.")

                messages = selected_ticket.get("messages", [])
                
                chat_html = '<div class="chat-container">'
                if not messages:
                    chat_html += '<div style="text-align:center; color:#64748b; font-size:0.85rem;">No messages yet. Send a message below to reach your technician.</div>'
                else:
                    for msg in messages:
                        sender = msg["sender"]
                        ts = msg["timestamp"].strftime("%I:%M %p")
                        text_body = msg["message"]
                        
                        if sender == "Employee":
                            chat_html += f"""
                            <div class="chat-msg-emp">
                                <div>{text_body}</div>
                                <span class="chat-meta">You (Employee) • {ts}</span>
                            </div>
                            """
                        elif sender == "IT Agent":
                            chat_html += f"""
                            <div class="chat-msg-agent">
                                <div>{text_body}</div>
                                <span class="chat-meta">IT Agent ({selected_ticket['assigned_agent']}) • {ts}</span>
                            </div>
                            """
                        else:
                            chat_html += f"""
                            <div class="chat-msg-sys">
                                ℹ️ {text_body} • <span style="opacity:0.7;">{ts}</span>
                            </div>
                            """
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)

                with st.form(f"emp_chat_form_{selected_ticket['ticket_id']}"):
                    emp_msg_input = st.text_input("Type message to IT Agent:", placeholder="Type your message or question here...")
                    send_btn = st.form_submit_button("Send Message", type="primary", use_container_width=True)

                if send_btn and emp_msg_input.strip():
                    selected_ticket["messages"].append({
                        "sender": "Employee",
                        "message": emp_msg_input.strip(),
                        "timestamp": datetime.now()
                    })
                    st.rerun()

    # ---------------------------------------------------------
    # VIEW 4: Complaint Report
    # ---------------------------------------------------------
    elif emp_nav == "📄 Complaint Report":
        st.header("📄 Complaint Report")
        st.caption("Official incident summary report and record documentation.")

        if not session_tickets:
            st.info("You haven't submitted any complaints yet. Use **New Complaint** to submit a support request.")
        else:
            ticket_options = [t["ticket_id"] + " - " + t["subject"] for t in session_tickets]
            chosen_str = st.selectbox("Select Ticket for Report Generation:", ticket_options)
            chosen_id = chosen_str.split(" - ")[0]
            t_rec = next((t for t in session_tickets if t["ticket_id"] == chosen_id), None)

            if t_rec:
                is_resolved = (t_rec["status"] == "Resolved")
                res_time_str = f"{t_rec['resolution_hours']:.1f} Hours" if is_resolved and t_rec.get("resolution_hours") is not None else "Resolution pending"
                sla_res_str = t_rec.get("sla_result", "Resolution pending") if is_resolved else "Resolution pending"
                res_at_str = t_rec["resolved_at"].strftime('%Y-%m-%d %H:%M:%S') if is_resolved and t_rec.get("resolved_at") else "Resolution pending"
                res_notes_str = t_rec.get("resolution_notes", "Resolved successfully") if is_resolved else "Resolution pending"

                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(51, 65, 85, 0.8); border-radius: 12px; padding: 24px; font-family: monospace;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(71, 85, 105, 0.6); padding-bottom: 12px; margin-bottom: 16px;">
                        <h3 style="margin: 0; color: #60a5fa;">IT SERVICE MANAGEMENT — COMPLAINT REPORT</h3>
                        <div>{get_status_badge(t_rec['status'])}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.9rem; line-height: 1.6;">
                        <div><strong>Ticket ID:</strong> {t_rec['ticket_id']}</div>
                        <div><strong>Issue:</strong> {t_rec['subject']}</div>
                        <div><strong>Category:</strong> {t_rec['category']}</div>
                        <div><strong>Priority:</strong> {t_rec['priority']}</div>
                        <div><strong>Assigned Agent:</strong> {t_rec['assigned_agent']}</div>
                        <div><strong>Created At:</strong> {t_rec['created_at'].strftime('%Y-%m-%d %H:%M:%S')}</div>
                        <div><strong>Response SLA:</strong> {t_rec['response_sla_hours']} Hours</div>
                        <div><strong>Resolution SLA:</strong> {t_rec['resolution_sla_hours']} Hours</div>
                        <div><strong>Status:</strong> {t_rec['status']}</div>
                        <div><strong>SLA Result:</strong> {sla_res_str}</div>
                        <div><strong>Resolution Time:</strong> {res_time_str}</div>
                        <div><strong>Resolution Notes:</strong> {res_notes_str}</div>
                    </div>
                    <hr style="border-color: rgba(71, 85, 105, 0.6); margin: 16px 0;">
                    <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;"><strong>Description:</strong> {t_rec['description']}</p>
                </div>
                """, unsafe_allow_html=True)

                st.write("")

                report_text = f"""IT SERVICE MANAGEMENT - COMPLAINT REPORT
==================================================
Ticket ID: {t_rec['ticket_id']}
Issue: {t_rec['subject']}
Description: {t_rec['description']}
Category: {t_rec['category']}
Priority: {t_rec['priority']}
Assigned Agent: {t_rec['assigned_agent']}
Created At: {t_rec['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
Response SLA: {t_rec['response_sla_hours']} Hours
Resolution SLA: {t_rec['resolution_sla_hours']} Hours
Status: {t_rec['status']}
SLA Result: {sla_res_str}
Resolution Time: {res_time_str}
Resolution Notes: {res_notes_str}
==================================================
"""
                col_down1, col_down2 = st.columns(2)
                with col_down1:
                    st.download_button(
                        label="📥 Download Report (.TXT)",
                        data=report_text,
                        file_name=f"{t_rec['ticket_id']}_report.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                with col_down2:
                    df_single = pd.DataFrame([{
                        "Ticket ID": t_rec["ticket_id"],
                        "Issue": t_rec["subject"],
                        "Category": t_rec["category"],
                        "Priority": t_rec["priority"],
                        "Assigned Agent": t_rec["assigned_agent"],
                        "Created At": t_rec["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                        "Response SLA": f"{t_rec['response_sla_hours']}h",
                        "Resolution SLA": f"{t_rec['resolution_sla_hours']}h",
                        "Status": t_rec["status"],
                        "SLA Result": sla_res_str,
                        "Resolution Time": res_time_str,
                        "Resolution Notes": res_notes_str
                    }])
                    csv_data = df_single.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Report (.CSV)",
                        data=csv_data,
                        file_name=f"{t_rec['ticket_id']}_report.csv",
                        mime="text/csv",
                        use_container_width=True
                    )


# -------------------------------------------------------------
# SCREEN 3: IT OPERATIONS CENTER
# -------------------------------------------------------------
def render_agent_dashboard():
    # Sidebar
    with st.sidebar:
        st.markdown("<span class='role-badge-ops'>🧑‍💼 IT Operations Center</span>", unsafe_allow_html=True)
        st.title("IT Operations")
        st.caption("Intelligent IT SLA Management")
        
        agent_nav = st.radio(
            "Operations Navigation",
            [
                "📊 Operations Overview",
                "🎫 Active Tickets",
                "🚨 Escalation Center",
                "👥 Agent Workload",
                "🔎 Historical Knowledge",
                "📈 Analytics"
            ],
            label_visibility="collapsed"
        )
        
        st.divider()
        if st.button("🔄 Switch Role", use_container_width=True):
            st.session_state["current_role"] = None
            st.rerun()
            
        render_sidebar_status()

    # Dynamic refresh of SLA status & escalation for live session tickets
    now = datetime.now()
    for t in st.session_state["session_tickets"]:
        if t["status"] != "Resolved":
            status, time_disp, rem_h = get_sla_status(t["resolution_deadline"], current_time=now)
            t["sla_status"] = status
            t["time_display"] = time_disp
            esc_res = check_escalation(
                priority=t["priority"],
                breach_risk=t["risk_percentage"],
                remaining_hours=rem_h,
                sla_status=status,
                agent_load=t["agent_new_load"],
                affected_users=t["affected_users"]
            )
            t["escalation_status"] = esc_res["escalation_status"]
            t["escalation_level"] = esc_res["escalation_level"]
            t["escalation_reasons"] = esc_res["reasons"]
            t["escalation_action"] = esc_res["recommended_action"]
            t["simulated_action"] = esc_res["simulated_action"]

    session_tickets = st.session_state["session_tickets"]
    all_total_tickets = len(df_historical) + len(session_tickets)
    
    # Historical calculations
    hist_open = int((df_historical["status"] == "Open").sum()) if "status" in df_historical.columns else 0
    hist_prog = int((df_historical["status"] == "In Progress").sum()) if "status" in df_historical.columns else 0
    hist_res = int((df_historical["status"] == "Resolved").sum()) if "status" in df_historical.columns else 0
    hist_breached = int((df_historical["sla_breached"] == True).sum()) if "sla_breached" in df_historical.columns else 0
    hist_critical = int((df_historical["priority"] == "Critical").sum()) if "priority" in df_historical.columns else 0
    
    # Session calculations
    sess_open = sum(1 for t in session_tickets if t["status"] == "Open")
    sess_prog = sum(1 for t in session_tickets if t["status"] == "In Progress")
    sess_res = sum(1 for t in session_tickets if t["status"] == "Resolved")
    sess_breached = sum(1 for t in session_tickets if "BREACHED" in t["sla_status"])
    sess_at_risk = sum(1 for t in session_tickets if "AT RISK" in t["sla_status"])
    sess_high_risk = sum(1 for t in session_tickets if t["risk_level"] in ["HIGH", "CRITICAL"])
    
    total_open = hist_open + sess_open
    total_prog = hist_prog + sess_prog
    total_res = hist_res + sess_res
    total_breached = hist_breached + sess_breached
    total_met = (all_total_tickets - total_breached)
    overall_compliance = (total_met / all_total_tickets * 100) if all_total_tickets > 0 else 100.0
    total_high_risk = hist_critical + sess_high_risk

    # ---------------------------------------------------------
    # VIEW 1: Operations Overview
    # ---------------------------------------------------------
    if agent_nav == "📊 Operations Overview":
        # Header with live status badge
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">IT Operations Center</h1>
                <p style="color: #94a3b8; margin: 4px 0 0 0;">Real-time service health, proactive SLA monitoring, and automated incident triage</p>
            </div>
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; color: #34d399; font-weight: 600;">
                ● All systems operational
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Top KPI Cards Grid
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">TOTAL TICKETS</div>
                <div class="kpi-value">{all_total_tickets:,}</div>
                <div class="kpi-sub">Historical + Session</div>
            </div>
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">OPEN</div>
                <div class="kpi-value" style="color:#60a5fa;">{total_open:,}</div>
                <div class="kpi-sub">Unassigned / Pending</div>
            </div>
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">IN PROGRESS</div>
                <div class="kpi-value" style="color:#fbbf24;">{total_prog:,}</div>
                <div class="kpi-sub">Active in queue</div>
            </div>
            <div class="kpi-card kpi-green">
                <div class="kpi-title">RESOLVED</div>
                <div class="kpi-value" style="color:#34d399;">{total_res:,}</div>
                <div class="kpi-sub">Closed successfully</div>
            </div>
            <div class="kpi-card kpi-red">
                <div class="kpi-title">SLA BREACHED</div>
                <div class="kpi-value" style="color:#f87171;">{total_breached:,}</div>
                <div class="kpi-sub">Missed target SLA</div>
            </div>
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">AT RISK</div>
                <div class="kpi-value" style="color:#fbbf24;">{sess_at_risk}</div>
                <div class="kpi-sub">Approaching deadline</div>
            </div>
            <div class="kpi-card kpi-green" style="background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.5);">
                <div class="kpi-title" style="color:#34d399;">SLA COMPLIANCE</div>
                <div class="kpi-value" style="color:#34d399;">{overall_compliance:.1f}%</div>
                <div class="kpi-sub" style="color:#a7f3d0;">Target: &ge; 85.0%</div>
            </div>
            <div class="kpi-card kpi-purple">
                <div class="kpi-title">HIGH/CRITICAL RISK</div>
                <div class="kpi-value" style="color:#c084fc;">{total_high_risk:,}</div>
                <div class="kpi-sub">Requiring supervision</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ⏱️ SLA Monitoring Section
        st.subheader("⏱️ SLA Monitoring")
        col_sla1, col_sla2, col_sla3, col_sla4 = st.columns(4)
        with col_sla1:
            st.metric("SLA Compliance %", f"{overall_compliance:.1f}%", delta="Normal Health")
        with col_sla2:
            st.metric("SLA Met Tickets", f"{total_met:,}")
        with col_sla3:
            st.metric("SLA Breached Tickets", f"{total_breached:,}")
        with col_sla4:
            st.metric("Live Session At Risk", sess_at_risk)

        st.write("")

        # Live session stream
        if session_tickets:
            st.markdown(f"##### ⚡ Live Incoming Triage Activity ({len(session_tickets)} Session Tickets)")
            stream_html = """
            <div style="overflow-x: auto; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border: 1px solid rgba(51, 65, 85, 0.6); padding: 10px; margin-bottom: 20px;">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                    <thead>
                        <tr style="border-bottom: 1px solid rgba(71, 85, 105, 0.6); color: #94a3b8;">
                            <th style="padding: 10px;">Ticket ID</th>
                            <th style="padding: 10px;">Subject</th>
                            <th style="padding: 10px;">Category</th>
                            <th style="padding: 10px;">Priority</th>
                            <th style="padding: 10px;">Agent</th>
                            <th style="padding: 10px;">Breach Risk</th>
                            <th style="padding: 10px;">Escalation</th>
                            <th style="padding: 10px;">SLA Status</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for t in session_tickets[:5]:
                stream_html += f"""
                    <tr style="border-bottom: 1px solid rgba(51, 65, 85, 0.4); color: #f1f5f9;">
                        <td style="padding: 10px; font-weight: 600; color: #60a5fa;">{t['ticket_id']}</td>
                        <td style="padding: 10px;">{t['subject']}</td>
                        <td style="padding: 10px;"><span class="badge badge-slate">{t['category']}</span></td>
                        <td style="padding: 10px;">{get_priority_badge(t['priority'])}</td>
                        <td style="padding: 10px; color: #cbd5e1;">{t['assigned_agent']}</td>
                        <td style="padding: 10px;">{get_risk_badge(t['risk_level'])} ({t['risk_percentage']}%)</td>
                        <td style="padding: 10px;">{get_escalation_badge(t['escalation_level'])}</td>
                        <td style="padding: 10px;">{get_sla_badge(t['sla_status'])}</td>
                    </tr>
                """
            stream_html += "</tbody></table></div>"
            st.markdown(stream_html, unsafe_allow_html=True)
            st.divider()

        # Operational Charts Grid (Compact Rows)
        st.subheader("📊 Operational Analytics Grid")
        
        # Row 1
        col_r1_1, col_r1_2 = st.columns(2)
        with col_r1_1:
            st.markdown("##### Category Distribution")
            cat_counts = df_historical["category"].value_counts()
            st.bar_chart(cat_counts)
        with col_r1_2:
            st.markdown("##### Priority Distribution")
            pri_counts = df_historical["priority"].value_counts()
            st.bar_chart(pri_counts)

        # Row 2
        col_r2_1, col_r2_2 = st.columns(2)
        with col_r2_1:
            st.markdown("##### Ticket Status Distribution")
            status_counts = df_historical["status"].value_counts()
            st.bar_chart(status_counts)
        with col_r2_2:
            st.markdown("##### SLA Met vs Breached")
            sla_dist = pd.Series({
                "SLA Met": total_met,
                "SLA Breached": total_breached
            })
            st.bar_chart(sla_dist)

        # Row 3
        col_r3_1, col_r3_2 = st.columns(2)
        with col_r3_1:
            st.markdown("##### Agent Workload")
            chart_pool_df = pd.DataFrame([
                {"Agent": a["name"], "Tickets in Queue": a["load"]}
                for a in st.session_state["agent_pool"]
            ]).set_index("Agent")
            st.bar_chart(chart_pool_df)
        with col_r3_2:
            st.markdown("##### Historical Breach Rate by Priority")
            if "priority" in df_historical.columns and "sla_breached" in df_historical.columns:
                pri_breach = df_historical.groupby("priority")["sla_breached"].mean().round(2) * 100
                st.bar_chart(pri_breach)

    # ---------------------------------------------------------
    # VIEW 2: Active Tickets Queue & AI Decision Trail
    # ---------------------------------------------------------
    elif agent_nav == "🎫 Active Tickets":
        st.header("🎫 Active Tickets")
        st.caption("Manage live queue operations, inspect transparent 🧠 AI Decision Trails, and update ticket statuses.")

        col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns(6)
        with col_f1:
            f_cat = st.selectbox("Category:", ["All", "Network", "Hardware", "Software", "Email", "Printer", "Security", "Access/Account"])
        with col_f2:
            f_pri = st.selectbox("Priority:", ["All", "Critical", "High", "Medium", "Low"])
        with col_f3:
            f_stat = st.selectbox("Status:", ["All", "Open", "In Progress", "Resolved"])
        with col_f4:
            f_agent = st.selectbox("Agent:", ["All"] + [a["name"] for a in st.session_state["agent_pool"]])
        with col_f5:
            f_sla = st.selectbox("SLA Status:", ["All", "ON TRACK", "AT RISK", "BREACHED"])
        with col_f6:
            f_risk = st.selectbox("Risk Level:", ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"])

        if session_tickets:
            st.markdown("#### ⚡ Live Incoming Tickets (Session)")
            sess_filtered = session_tickets
            if f_cat != "All":
                sess_filtered = [t for t in sess_filtered if t["category"] == f_cat]
            if f_pri != "All":
                sess_filtered = [t for t in sess_filtered if t["priority"] == f_pri]
            if f_stat != "All":
                sess_filtered = [t for t in sess_filtered if t["status"] == f_stat]
            if f_agent != "All":
                sess_filtered = [t for t in sess_filtered if t["assigned_agent"] == f_agent]
            if f_sla != "All":
                sess_filtered = [t for t in sess_filtered if f_sla in t["sla_status"]]
            if f_risk != "All":
                sess_filtered = [t for t in sess_filtered if t["risk_level"] == f_risk]

            if sess_filtered:
                table_html = """
                <div style="overflow-x: auto; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border: 1px solid rgba(51, 65, 85, 0.6); padding: 10px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(71, 85, 105, 0.6); color: #94a3b8;">
                                <th style="padding: 10px;">Ticket ID</th>
                                <th style="padding: 10px;">Subject</th>
                                <th style="padding: 10px;">Category</th>
                                <th style="padding: 10px;">Priority</th>
                                <th style="padding: 10px;">Status</th>
                                <th style="padding: 10px;">Assigned Agent</th>
                                <th style="padding: 10px;">SLA Status</th>
                                <th style="padding: 10px;">Risk</th>
                                <th style="padding: 10px;">Created</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                for t in sess_filtered:
                    table_html += f"""
                        <tr style="border-bottom: 1px solid rgba(51, 65, 85, 0.4); color: #f1f5f9;">
                            <td style="padding: 10px; font-weight: 600; color: #60a5fa;">{t['ticket_id']}</td>
                            <td style="padding: 10px;">{t['subject']}</td>
                            <td style="padding: 10px;"><span class="badge badge-slate">{t['category']}</span></td>
                            <td style="padding: 10px;">{get_priority_badge(t['priority'])}</td>
                            <td style="padding: 10px;">{get_status_badge(t['status'])}</td>
                            <td style="padding: 10px; color: #cbd5e1;">{t['assigned_agent']}</td>
                            <td style="padding: 10px;">{get_sla_badge(t['sla_status'])}</td>
                            <td style="padding: 10px;">{get_risk_badge(t['risk_level'])} ({t['risk_percentage']}%)</td>
                            <td style="padding: 10px; color: #94a3b8;">{t['created_at'].strftime('%I:%M %p')}</td>
                        </tr>
                    """
                table_html += "</tbody></table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.info("All tickets are currently under control matching the selected filters.")
        else:
            st.info("All tickets are currently under control. Submit a complaint in the Employee Portal or use Demo Mode to populate tickets.")

        st.divider()

        # Operational Ticket Inspector & Customer Communication
        if session_tickets:
            st.subheader("🔍 Operational Ticket Inspector")
            t_opts = [t["ticket_id"] + " - " + t["subject"] for t in session_tickets]
            inspected_str = st.selectbox("Select Session Ticket to Inspect & Manage:", t_opts)
            inspected_id = inspected_str.split(" - ")[0]
            inspected_t = next((t for t in session_tickets if t["ticket_id"] == inspected_id), None)

            if inspected_t:
                # Top Overview Card
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(51, 65, 85, 0.75); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(71, 85, 105, 0.5); padding-bottom: 10px; margin-bottom: 14px;">
                        <div>
                            <span style="font-size: 1.3rem; font-weight: 700; color: #60a5fa;">{inspected_t['ticket_id']}</span>
                            <span style="margin-left: 10px;">{get_status_badge(inspected_t['status'])}</span>
                            <span style="margin-left: 6px;">{get_priority_badge(inspected_t['priority'])}</span>
                        </div>
                        <div>
                            {get_risk_badge(inspected_t['risk_level'])} | {get_sla_badge(inspected_t['sla_status'])}
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; font-size: 0.9rem; margin-bottom: 12px;">
                        <div><strong style="color:#94a3b8;">Subject:</strong><br>{inspected_t['subject']}</div>
                        <div><strong style="color:#94a3b8;">Category:</strong><br>{inspected_t['category']}</div>
                        <div><strong style="color:#94a3b8;">Assigned Agent:</strong><br>{inspected_t['assigned_agent']} (Queue: {inspected_t['agent_new_load']} open)</div>
                        <div><strong style="color:#94a3b8;">Affected Users:</strong><br>{inspected_t['affected_users']}</div>
                        <div><strong style="color:#94a3b8;">Resolution Target:</strong><br>{inspected_t['resolution_deadline'].strftime('%I:%M %p')}</div>
                        <div><strong style="color:#94a3b8;">Time Remaining:</strong><br>{inspected_t['time_display']}</div>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; font-size: 0.88rem; color: #cbd5e1;">
                        <strong>Description:</strong> {inspected_t['description']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Status Manager
                st.markdown("#### ⚙️ Update Ticket Status")
                col_stat_sel, col_stat_btn = st.columns([2, 1])
                with col_stat_sel:
                    current_status_idx = ["Open", "In Progress", "Resolved"].index(inspected_t["status"])
                    new_status_val = st.selectbox(
                        "Change Status:",
                        ["Open", "In Progress", "Resolved"],
                        index=current_status_idx,
                        key=f"status_select_{inspected_t['ticket_id']}"
                    )
                with col_stat_btn:
                    st.write("")
                    st.write("")
                    if st.button("💾 Apply Status Update", key=f"btn_update_stat_{inspected_t['ticket_id']}", use_container_width=True):
                        if new_status_val != inspected_t["status"]:
                            inspected_t["status"] = new_status_val
                            if new_status_val == "Resolved":
                                resolved_time = datetime.now()
                                inspected_t["resolved_at"] = resolved_time
                                res_h = round((resolved_time - inspected_t["created_at"]).total_seconds() / 3600.0, 2)
                                inspected_t["resolution_hours"] = res_h
                                sla_met = bool(res_h <= inspected_t["resolution_sla_hours"])
                                inspected_t["sla_result"] = "SLA Met" if sla_met else "SLA Breached"
                                
                                inspected_t["messages"].append({
                                    "sender": "System",
                                    "message": f"Ticket marked as Resolved by IT Agent ({inspected_t['assigned_agent']}). Outcome: {inspected_t['sla_result']} (Resolution Time: {res_h:.1f} hrs).",
                                    "timestamp": resolved_time
                                })
                            else:
                                inspected_t["messages"].append({
                                    "sender": "System",
                                    "message": f"Ticket status updated to '{new_status_val}' by IT Agent ({inspected_t['assigned_agent']}).",
                                    "timestamp": datetime.now()
                                })
                            st.success(f"Status updated to '{new_status_val}'.")
                            st.rerun()

                st.divider()

                # Customer Communication Channel for Agent
                st.markdown("#### 💬 Customer Communication")
                st.caption(f"Direct communication thread with employee for Ticket {inspected_t['ticket_id']}.")

                messages = inspected_t.get("messages", [])
                chat_html = '<div class="chat-container">'
                if not messages:
                    chat_html += '<div style="text-align:center; color:#64748b; font-size:0.85rem;">No messages in this ticket conversation yet.</div>'
                else:
                    for msg in messages:
                        sender = msg["sender"]
                        ts = msg["timestamp"].strftime("%I:%M %p")
                        text_body = msg["message"]
                        
                        if sender == "Employee":
                            chat_html += f"""
                            <div class="chat-msg-emp">
                                <div>{text_body}</div>
                                <span class="chat-meta">Employee • {ts}</span>
                            </div>
                            """
                        elif sender == "IT Agent":
                            chat_html += f"""
                            <div class="chat-msg-agent">
                                <div>{text_body}</div>
                                <span class="chat-meta">You ({inspected_t['assigned_agent']}) • {ts}</span>
                            </div>
                            """
                        else:
                            chat_html += f"""
                            <div class="chat-msg-sys">
                                ℹ️ {text_body} • <span style="opacity:0.7;">{ts}</span>
                            </div>
                            """
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)

                with st.form(f"agent_chat_form_{inspected_t['ticket_id']}"):
                    agent_reply_input = st.text_input("Send reply to employee:", placeholder="Type support response or update...")
                    send_reply_btn = st.form_submit_button("Send Reply", type="primary", use_container_width=True)

                if send_reply_btn and agent_reply_input.strip():
                    inspected_t["messages"].append({
                        "sender": "IT Agent",
                        "message": agent_reply_input.strip(),
                        "timestamp": datetime.now()
                    })
                    st.rerun()

                st.divider()

                # 🧠 AI DECISION TRAIL (EXPANDABLE TIMELINE)
                with st.expander("🧠 AI Decision Trail (Step-by-Step Explainability)", expanded=True):
                    st.caption("Transparent reasoning for automated triage, priority scoring, routing, and escalation.")

                    st.markdown(f"""
                    <div class="trail-step">
                        <strong><span class="trail-num">1</span> CATEGORY CLASSIFICATION</strong><br>
                        <strong>Predicted Category:</strong> <code>{inspected_t['category']}</code><br>
                        <span style="color:#cbd5e1; font-size:0.88rem;"><strong>Reason:</strong> {inspected_t['category_explanation']}</span>
                    </div>
                    
                    <div class="trail-step">
                        <strong><span class="trail-num">2</span> PRIORITY SCORING</strong><br>
                        <strong>Predicted Priority:</strong> {get_priority_badge(inspected_t['priority'])}<br>
                        <span style="color:#cbd5e1; font-size:0.88rem;"><strong>Reason:</strong> {inspected_t['priority_explanation']}</span>
                    </div>
                    
                    <div class="trail-step">
                        <strong><span class="trail-num">3</span> INTELLIGENT ROUTING</strong><br>
                        <strong>Assigned Agent:</strong> <code>{inspected_t['assigned_agent']}</code> (Skills: {', '.join(inspected_t['agent_skills'])})<br>
                        <span style="color:#cbd5e1; font-size:0.88rem;"><strong>Reason:</strong> {inspected_t['assignment_explanation']}</span>
                    </div>
                    
                    <div class="trail-step">
                        <strong><span class="trail-num">4</span> SLA TARGET POLICY</strong><br>
                        <strong>Response SLA:</strong> <code>{inspected_t['response_sla_hours']}h</code> | <strong>Resolution SLA:</strong> <code>{inspected_t['resolution_sla_hours']}h</code><br>
                        <span style="color:#cbd5e1; font-size:0.88rem;"><strong>Reason:</strong> {inspected_t['sla_explanation']}</span>
                    </div>
                    
                    <div class="trail-step">
                        <strong><span class="trail-num">5</span> SLA BREACH-RISK PREDICTION</strong><br>
                        <strong>Risk Estimate:</strong> {get_risk_badge(inspected_t['risk_level'])} ({inspected_t['risk_percentage']}%)<br>
                        <span style="color:#cbd5e1; font-size:0.88rem;"><strong>Reason:</strong> {inspected_t['risk_explanation']}</span>
                    </div>
                    
                    <div class="trail-step">
                        <strong><span class="trail-num">6</span> HISTORICAL KNOWLEDGE MATCH</strong><br>
                        <strong>Finding:</strong> <span style="color:#cbd5e1; font-size:0.88rem;">{inspected_t['similarity_explanation']}</span>
                    </div>
                    
                    <div class="trail-step" style="border-left-color: #ef4444;">
                        <strong><span class="trail-num" style="background:#ef4444;">7</span> AUTOMATED ESCALATION DECISION</strong><br>
                        <strong>Escalation Level:</strong> {get_escalation_badge(inspected_t['escalation_level'])}<br>
                        <strong>Recommended Action:</strong> <code>{inspected_t['escalation_action']}</code><br>
                        <span style="color:#cbd5e1; font-size:0.88rem;"><strong>Trigger Reason:</strong> {inspected_t['escalation_explanation']}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VIEW 3: Escalation Center
    # ---------------------------------------------------------
    elif agent_nav == "🚨 Escalation Center":
        st.header("🚨 Incident Escalation Center")
        st.caption("Active supervisor queue for live at-risk incidents and historical SLA alert records.")

        tab_live_esc, tab_hist_esc = st.tabs(["🚨 LIVE ESCALATIONS", "📊 HISTORICAL SLA ALERTS"])

        # TAB 1: Live Escalations
        with tab_live_esc:
            st.subheader("Live Escalations (Active Session)")
            
            live_escalations = [
                t for t in session_tickets
                if t["escalation_status"] in ["ESCALATION REQUIRED", "WARNING"]
            ]

            if not live_escalations:
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 20px; margin: 10px 0;">
                    <h4 style="color: #34d399; margin: 0 0 6px 0;">✓ No active escalations</h4>
                    <p style="color: #94a3b8; margin: 0;">All monitored live tickets are currently within their escalation thresholds.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for esc_t in live_escalations:
                    level = esc_t["escalation_level"]
                    is_critical = (level == "CRITICAL ESCALATION")
                    border_color = "#ef4444" if is_critical else "#f59e0b"
                    bg_color = "rgba(239, 68, 68, 0.1)" if is_critical else "rgba(245, 158, 11, 0.1)"
                    
                    st.markdown(f"""
                    <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 10px; margin-bottom: 12px;">
                            <div>
                                <span style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">🚨 [{level}] Ticket <code>{esc_t['ticket_id']}</code>: {esc_t['subject']}</span>
                            </div>
                            <div>
                                {get_priority_badge(esc_t['priority'])} | {get_risk_badge(esc_t['risk_level'])} ({esc_t['risk_percentage']}%)
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; font-size: 0.9rem; margin-bottom: 12px;">
                            <div><strong style="color:#94a3b8;">Assigned Agent:</strong><br>{esc_t['assigned_agent']}</div>
                            <div><strong style="color:#94a3b8;">Time Remaining:</strong><br>{esc_t['time_display']}</div>
                            <div><strong style="color:#94a3b8;">SLA Status:</strong><br>{get_sla_badge(esc_t['sla_status'])}</div>
                            <div><strong style="color:#94a3b8;">Current Status:</strong><br>{get_status_badge(esc_t['status'])}</div>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; font-size: 0.9rem;">
                            <strong style="color:#f87171;">Action:</strong> <strong>{esc_t['escalation_action']}</strong><br>
                            <span style="color:#cbd5e1;"><strong>Reason:</strong> {esc_t['escalation_reasons'][0] if esc_t.get('escalation_reasons') else esc_t.get('escalation_reason', '')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # TAB 2: Historical SLA Alerts
        with tab_hist_esc:
            st.subheader("Historical SLA Alerts")
            st.caption("Historical incidents from tickets.csv that triggered SLA alerts (breached SLA, critical priority, or high queue depth).")

            hist_alert_filter = st.radio(
                "Filter Historical Alerts:",
                ["All Breached Tickets (sla_breached == 1)", "Critical Priority Incidents", "High Queue Depth (>= 6)"],
                horizontal=True
            )

            if hist_alert_filter == "All Breached Tickets (sla_breached == 1)":
                hist_alert_df = df_historical[df_historical["sla_breached"] == True]
            elif hist_alert_filter == "Critical Priority Incidents":
                hist_alert_df = df_historical[df_historical["priority"] == "Critical"]
            else:
                hist_alert_df = df_historical[df_historical["agent_queue_depth"] >= 6]

            st.write(f"**Found {len(hist_alert_df)} Historical SLA Alert Records:**")
            
            hist_disp_cols = [
                col for col in [
                    "ticket_id", "subject", "category", "priority", "assigned_agent",
                    "sla_hours", "resolution_hours", "sla_breached", "resolution_notes"
                ] if col in hist_alert_df.columns
            ]
            st.dataframe(hist_alert_df[hist_disp_cols].head(100), use_container_width=True, height=400, hide_index=True)

    # ---------------------------------------------------------
    # VIEW 4: Agent Workload
    # ---------------------------------------------------------
    elif agent_nav == "👥 Agent Workload":
        st.header("👥 Agent Workload & Routing Pool")
        st.caption("Real-time technician queue depths, domain skill competencies, and automated load balancing.")

        col_w1, col_w2 = st.columns([1, 1])
        with col_w1:
            st.subheader("Agent Pool Status")
            
            for a in st.session_state["agent_pool"]:
                load = a["load"]
                if load >= 7:
                    status_badge = '<span class="badge badge-red">HIGH WORKLOAD</span>'
                    card_border = "#ef4444"
                elif load >= 4:
                    status_badge = '<span class="badge badge-amber">MODERATE WORKLOAD</span>'
                    card_border = "#f59e0b"
                else:
                    status_badge = '<span class="badge badge-green">LOW WORKLOAD</span>'
                    card_border = "#10b981"

                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(51, 65, 85, 0.7); border-left: 4px solid {card_border}; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 1.1rem; color: #f8fafc;">{a['name']}</strong>
                        {status_badge}
                    </div>
                    <div style="font-size: 0.88rem; color: #94a3b8; margin-top: 6px;">
                        <strong>Skills:</strong> {', '.join(a['skills'])}<br>
                        <strong>Active Queue:</strong> <span style="font-size: 1.05rem; font-weight: 700; color: #f8fafc;">{load}</span> tickets in queue
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("🔄 Reset Agent Workloads to Default", use_container_width=True):
                st.session_state["agent_pool"] = get_initial_agents()
                st.rerun()

        with col_w2:
            st.subheader("Current Queue Distribution")
            chart_df = pd.DataFrame([
                {"Agent": a["name"], "Tickets in Queue": a["load"]}
                for a in st.session_state["agent_pool"]
            ]).set_index("Agent")
            st.bar_chart(chart_df)

    # ---------------------------------------------------------
    # VIEW 5: Historical Knowledge Base
    # ---------------------------------------------------------
    elif agent_nav == "🔎 Historical Knowledge":
        st.header("🔎 Historical Knowledge Base")
        st.caption("Search across 1,000 historical IT service records, resolution notes, and SLA outcomes.")

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            search_query = st.text_input("🔍 Search by Ticket ID, Subject, Description, or Symptoms:", placeholder="e.g. VPN, Outlook, BSOD, Okta, printer jam, crash...")
        with col_s2:
            kb_cat_filter = st.selectbox("Category Filter:", ["All", "Network", "Hardware", "Software", "Email", "Printer", "Security", "Access/Account"])

        kb_df = df_historical
        if kb_cat_filter != "All":
            kb_df = kb_df[kb_df["category"] == kb_cat_filter]

        if search_query.strip():
            query_mask = (
                kb_df["subject"].str.contains(search_query, case=False, na=False) |
                kb_df["description"].str.contains(search_query, case=False, na=False) |
                kb_df["ticket_id"].str.contains(search_query, case=False, na=False) |
                kb_df["resolution_notes"].str.contains(search_query, case=False, na=False)
            )
            kb_df = kb_df[query_mask]

        if kb_df.empty:
            st.info("No matching historical tickets found. Try submitting a more detailed description or changing your search terms.")
        else:
            st.markdown(f"**Found {len(kb_df)} Historical Matching Records:**")
            kb_cols = ["ticket_id", "subject", "category", "priority", "resolution_notes", "resolution_hours", "sla_breached"]
            st.dataframe(kb_df[[c for c in kb_cols if c in kb_df.columns]].head(100), use_container_width=True, height=450, hide_index=True)

    # ---------------------------------------------------------
    # VIEW 6: Analytics
    # ---------------------------------------------------------
    elif agent_nav == "📈 Analytics":
        st.header("📈 SLA Compliance & Performance Analytics")
        st.caption("Comprehensive historical and live operational insights across service tiers, categories, and priority levels.")

        # KPI Metrics
        avg_res_h = float(df_historical["resolution_hours"].mean()) if "resolution_hours" in df_historical.columns else 0.0
        breach_pct = float((df_historical["sla_breached"] == True).mean()) * 100.0 if "sla_breached" in df_historical.columns else 0.0

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">TOTAL TICKETS ANALYZED</div>
                <div class="kpi-value">{all_total_tickets:,}</div>
                <div class="kpi-sub">Reference knowledge base</div>
            </div>
            <div class="kpi-card kpi-green">
                <div class="kpi-title">OVERALL SLA COMPLIANCE</div>
                <div class="kpi-value" style="color:#34d399;">{overall_compliance:.1f}%</div>
                <div class="kpi-sub">{total_met:,} Met vs {total_breached:,} Breached</div>
            </div>
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">AVG RESOLUTION TIME</div>
                <div class="kpi-value" style="color:#fbbf24;">{avg_res_h:.1f}h</div>
                <div class="kpi-sub">Mean historical resolution</div>
            </div>
            <div class="kpi-card kpi-red">
                <div class="kpi-title">HISTORICAL BREACH RATE</div>
                <div class="kpi-value" style="color:#f87171;">{breach_pct:.1f}%</div>
                <div class="kpi-sub">Baseline risk factor</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Detailed Charts
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.subheader("Category Distribution")
            st.bar_chart(df_historical["category"].value_counts())
        with col_an2:
            st.subheader("Priority Distribution")
            st.bar_chart(df_historical["priority"].value_counts())

        col_an3, col_an4 = st.columns(2)
        with col_an3:
            st.subheader("Ticket Status Distribution")
            st.bar_chart(df_historical["status"].value_counts())
        with col_an4:
            st.subheader("SLA Met vs Breached")
            sla_dist = pd.Series({
                "SLA Met": total_met,
                "SLA Breached": total_breached
            })
            st.bar_chart(sla_dist)

        st.divider()
        col_an5, col_an6 = st.columns(2)
        with col_an5:
            st.subheader("Agent Workload Distribution")
            chart_pool_df = pd.DataFrame([
                {"Agent": a["name"], "Queue Load": a["load"]}
                for a in st.session_state["agent_pool"]
            ]).set_index("Agent")
            st.bar_chart(chart_pool_df)
        with col_an6:
            st.subheader("Resolution Time by Category (Hours)")
            if "category" in df_historical.columns and "resolution_hours" in df_historical.columns:
                cat_time = df_historical.groupby("category")["resolution_hours"].mean().round(1)
                st.bar_chart(cat_time)


# -------------------------------------------------------------
# MAIN CONTROLLER
# -------------------------------------------------------------
def main():
    if st.session_state["current_role"] == "employee":
        render_employee_dashboard()
    elif st.session_state["current_role"] == "agent":
        render_agent_dashboard()
    else:
        render_landing_screen()

if __name__ == "__main__":
    main()
