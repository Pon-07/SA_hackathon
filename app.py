# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import io
import textwrap

# Import Core Pipeline Modules
from categorization import (
    CATEGORY_KEYWORDS,
    categorize,
    explain_category,
    find_matched_keywords,
    format_keyword_name
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

# Helper function to render HTML cleanly without Markdown 4-space indentation code-block traps
def clean_markdown(html_str: str) -> None:
    cleaned = "\n".join(line.strip() for line in html_str.split("\n") if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

# Helper function to render styled HTML tables without markdown formatting glitches
def render_custom_table(headers: list, rows: list) -> None:
    header_html = "".join([f'<th style="padding: 10px 12px; color: #94a3b8; font-weight: 600; text-align: left;">{h}</th>' for h in headers])
    body_html = ""
    for r in rows:
        cells_html = "".join([f'<td style="padding: 10px 12px; border-bottom: 1px solid rgba(51, 65, 85, 0.4);">{cell}</td>' for cell in r])
        body_html += f'<tr style="color: #f1f5f9;">{cells_html}</tr>'
    
    table_html = f'<div style="overflow-x: auto; background: rgba(30, 41, 59, 0.5); border-radius: 10px; border: 1px solid rgba(51, 65, 85, 0.6); padding: 8px; margin-bottom: 16px;"><table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem;"><thead><tr style="border-bottom: 1px solid rgba(71, 85, 105, 0.6);">{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>'
    st.markdown(table_html, unsafe_allow_html=True)

clean_markdown("""
<style>
    /* Global Typography & SaaS Theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Modern Metric Containers */
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
    .chat-header-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 12px 12px 0 0;
        padding: 14px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(51, 65, 85, 0.5);
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 18px;
        background: rgba(15, 23, 42, 0.65);
        border-radius: 0 0 12px 12px;
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-top: none;
        margin-bottom: 16px;
        max-height: 440px;
        overflow-y: auto;
    }
    .chat-msg-emp {
        align-self: flex-end;
        max-width: 78%;
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
        color: #ffffff;
        padding: 11px 16px;
        border-radius: 16px 16px 2px 16px;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.25);
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .chat-msg-agent {
        align-self: flex-start;
        max-width: 78%;
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
        color: #ffffff;
        padding: 11px 16px;
        border-radius: 16px 16px 16px 2px;
        box-shadow: 0 2px 10px rgba(99, 102, 241, 0.25);
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .chat-msg-sys {
        align-self: center;
        max-width: 90%;
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(71, 85, 105, 0.5);
        color: #cbd5e1;
        padding: 7px 18px;
        border-radius: 20px;
        font-size: 0.82rem;
        text-align: center;
        margin: 4px 0;
    }
    .chat-meta {
        font-size: 0.72rem;
        opacity: 0.85;
        margin-top: 4px;
        display: block;
    }

    /* AI Decision Trail Card & Detailed Workflow Styling */
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
    .decision-card {
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(51, 65, 85, 0.75);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 6px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
    }
    .decision-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(51, 65, 85, 0.6);
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    .decision-step-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .decision-step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        background: #3b82f6;
        color: #ffffff;
        border-radius: 50%;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .decision-section {
        margin-bottom: 10px;
        font-size: 0.88rem;
        line-height: 1.5;
    }
    .decision-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-bottom: 3px;
        display: inline-block;
    }
    .decision-why {
        color: #cbd5e1;
        font-size: 0.88rem;
        background: rgba(15, 23, 42, 0.5);
        padding: 8px 12px;
        border-radius: 6px;
        border-left: 3px solid #3b82f6;
        margin-top: 3px;
    }
    .connector-arrow {
        text-align: center;
        color: #60a5fa;
        font-size: 1.2rem;
        margin: 2px 0 6px 0;
        opacity: 0.8;
    }
    .kw-chip {
        display: inline-block;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #93c5fd;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-family: monospace;
        margin: 2px 4px 2px 0;
    }
    .factor-item {
        display: inline-block;
        background: rgba(51, 65, 85, 0.5);
        border: 1px solid rgba(71, 85, 105, 0.5);
        color: #cbd5e1;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        margin: 3px 6px 3px 0;
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
""")

DATASET_PATH = Path(__file__).parent / "tickets.csv"

# -------------------------------------------------------------
# Data Loading & Caching (Read-Only 1,000 Historical Tickets)
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
# Session State Initialization (Fresh Session = Clean Empty State)
# -------------------------------------------------------------
def get_fresh_session_agents():
    """Start all agents with 0 workload in fresh session."""
    agents = get_initial_agents()
    for a in agents:
        a["load"] = 0
    return agents

if "current_role" not in st.session_state:
    st.session_state["current_role"] = None

if "agent_pool" not in st.session_state:
    st.session_state["agent_pool"] = get_fresh_session_agents()

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
    clean_markdown("""
    <div class="sys-status-widget">
        <strong style="color: #f1f5f9; letter-spacing: 0.5px; font-size: 0.75rem;">SYSTEM STATUS</strong><br>
        <span class="sys-dot-green">●</span> AI Triage Engine: <span style="color:#34d399;">Online</span><br>
        <span class="sys-dot-green">●</span> SLA Monitoring: <span style="color:#34d399;">Active</span><br>
        <span class="sys-dot-green">●</span> Routing Engine: <span style="color:#34d399;">Online</span><br>
        <span class="sys-dot-green">●</span> Knowledge Base: <span style="color:#60a5fa;">1,000 Tickets</span>
    </div>
    """)

# -------------------------------------------------------------
# Explainable AI Renderers (IT Operations Center & Employee Portal)
# -------------------------------------------------------------
def render_ai_decision_trail(ticket: dict) -> None:
    """
    Render transparent, step-by-step 7-stage Explainable AI decision trail.
    Structure per step: DECISION + WHY + EVIDENCE / FACTORS
    """
    # 1. Category Detection
    cat = ticket.get("category", "General")
    kws = ticket.get("category_keywords", [])
    cat_why = ticket.get("category_why", "Matched keywords from subject and description.")
    if kws:
        kw_html = "".join([f'<span class="kw-chip">{kw}</span>' for kw in kws])
        cat_evidence = f'<div style="margin-top:6px;"><span class="decision-label">Matched Keywords:</span><br>{kw_html}</div>'
    else:
        cat_evidence = '<div style="margin-top:6px; color:#94a3b8; font-size:0.84rem;"><em>No specific domain keywords matched in text. Applied fallback category classification.</em></div>'

    # 2. Priority Assessment
    pri = ticket.get("priority", "Medium")
    pri_score = ticket.get("priority_score", 0)
    pri_reasons = ticket.get("priority_reasons", [])
    pri_why = ticket.get("priority_why", "Determined by combined urgency signals, impact scale, and affected user count.")
    if pri_reasons:
        reasons_html = "".join([f'<span class="factor-item">{r}</span>' for r in pri_reasons])
        pri_evidence = f'<div style="margin-top:6px;"><span class="decision-label">Decision Factors & Signals (Score: {pri_score} pts):</span><br>{reasons_html}</div>'
    else:
        pri_evidence = f'<div style="margin-top:6px; color:#94a3b8; font-size:0.84rem;">Score: {pri_score} points (Calculated by prioritization engine)</div>'

    # 3. SLA Assignment
    resp_h = ticket.get("response_sla_hours", 4)
    res_h = ticket.get("resolution_sla_hours", 24)
    res_dead = ticket.get("resolution_deadline")
    dead_str = res_dead.strftime('%d %b %Y, %I:%M %p') if isinstance(res_dead, datetime) else str(res_dead)
    sla_why = f"{pri} priority follows the {pri} SLA policy ({resp_h}h response / {res_h}h resolution target)."
    sla_evidence = f"""
    <div style="margin-top:6px;">
        <span class="decision-label">SLA Policy Pipeline:</span><br>
        <div style="background:rgba(15,23,42,0.6); padding:8px 12px; border-radius:6px; font-size:0.85rem; color:#cbd5e1;">
            <strong style="color:#60a5fa;">{pri} Priority</strong> → <strong style="color:#38bdf8;">{resp_h}h Response / {res_h}h Resolution</strong> → <strong style="color:#34d399;">Target Deadline: {dead_str}</strong>
        </div>
    </div>
    """

    # 4. Intelligent Routing
    agent = ticket.get("assigned_agent", "Agent_01")
    skills = ticket.get("agent_skills", [])
    prev_load = ticket.get("agent_previous_load", 0)
    new_load = ticket.get("agent_new_load", 1)
    is_skill = ticket.get("is_skill_matched", True)
    skills_str = ", ".join(skills) if skills else "General IT"
    
    if is_skill:
        routing_why = f"Assigned to eligible specialist {agent} with verified {cat} competency and lowest active workload ({prev_load} tickets)."
    else:
        routing_why = f"No direct skill match for {cat}; routed to least-loaded available technician {agent} ({prev_load} tickets)."

    routing_evidence = f"""
    <div style="margin-top:6px;">
        <span class="decision-label">Workload & Skill Verification:</span><br>
        <span class="factor-item">🎯 Skill Match: <strong>{cat}</strong> {'✓ Verified' if is_skill else '(Fallback)'}</span>
        <span class="factor-item">🛠️ Agent Competencies: {skills_str}</span>
        <span class="factor-item">📊 Queue Workload: {prev_load} active tickets (Updated to {new_load})</span>
    </div>
    """

    # 5. Breach Risk Assessment
    risk_pct = ticket.get("risk_percentage", 10)
    risk_lvl = ticket.get("risk_level", "LOW")
    risk_reasons = ticket.get("risk_reasons", [])
    risk_border = "#ef4444" if risk_lvl in ["CRITICAL", "HIGH"] else "#f59e0b" if risk_lvl == "MEDIUM" else "#10b981"
    risk_why = ticket.get("risk_why")
    if not risk_why:
        if risk_lvl in ["CRITICAL", "HIGH"]:
            risk_why = "Risk is elevated because the ticket has high operational impact, tight SLA resolution window, or heavy agent load."
        elif risk_lvl == "MEDIUM":
            risk_why = "Moderate risk detected due to standard priority timeline and active queue commitments."
        else:
            risk_why = "Risk is low because the ticket has sufficient SLA buffer and manageable technician queue load."

    if risk_reasons:
        risk_reasons_html = "".join([f'<span class="factor-item">{r}</span>' for r in risk_reasons])
        risk_evidence = f'<div style="margin-top:6px;"><span class="decision-label">Multi-Factor Risk Breakdown:</span><br>{risk_reasons_html}</div>'
    else:
        risk_evidence = '<div style="margin-top:6px; color:#94a3b8; font-size:0.84rem;">Computed by predictive breach risk engine based on priority, queue depth, and remaining SLA.</div>'

    # 6. Historical Similarity
    top_sim = ticket.get("top_similar")
    if not top_sim and ticket.get("similar_records"):
        top_sim = ticket["similar_records"][0]
        
    if top_sim:
        sim_id = top_sim.get("ticket_id", "TKT-0000")
        sim_sub = top_sim.get("subject", "Historical Support Record")
        sim_cat = top_sim.get("category", "General")
        sim_pct = top_sim.get("similarity_percentage", "0%")
        sim_res = top_sim.get("resolution_notes", "Resolution notes recorded in historical archive.")
        
        sim_why = "TF-IDF similarity identified this historical ticket as the closest match based on the subject and description."
        sim_evidence = f"""
        <div style="margin-top:6px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <span class="decision-label">Closest Historical Match:</span>
                <span class="badge badge-purple" style="font-size:0.7rem;">HISTORICAL REFERENCE</span>
            </div>
            <div style="background:rgba(15,23,42,0.65); border:1px solid rgba(51,65,85,0.6); padding:10px 14px; border-radius:8px; font-size:0.86rem; color:#cbd5e1;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <strong style="color:#60a5fa;">{sim_sub}</strong>
                    <span style="color:#94a3b8; font-family:monospace;">{sim_id} ({sim_cat})</span>
                </div>
                <div style="color:#38bdf8; font-weight:600; font-size:0.82rem; margin-bottom:6px;">TF-IDF Cosine Similarity: {sim_pct}</div>
                <div style="color:#cbd5e1; border-top:1px solid rgba(71,85,105,0.4); padding-top:6px; font-size:0.83rem;">
                    <strong style="color:#34d399;">Verified Resolution:</strong> {sim_res}
                </div>
            </div>
        </div>
        """
    else:
        sim_why = "Query text matched against 1,000 historical repository records via TF-IDF vectorizer."
        sim_evidence = '<div style="margin-top:6px; color:#94a3b8; font-size:0.84rem;">No matching historical record met similarity threshold.</div>'

    # 7. Escalation Decision
    esc_lvl = ticket.get("escalation_level", "NO ESCALATION")
    esc_status = ticket.get("escalation_status", "NO ESCALATION")
    esc_action = ticket.get("escalation_action", "No escalation required. Ticket is currently on track.")
    esc_reasons = ticket.get("escalation_reasons", [])
    sim_action = ticket.get("simulated_action", "")
    esc_border = "#ef4444" if "CRITICAL" in esc_lvl else "#f59e0b" if "WARNING" in esc_lvl or "REQUIRED" in esc_lvl else "#10b981"
    
    if "CRITICAL" in esc_lvl:
        esc_why = "Critical escalation triggered due to imminent SLA breach threshold, critical business impact, or high queue risk."
    elif "WARNING" in esc_lvl or "REQUIRED" in esc_lvl:
        esc_why = "Warning escalation active: elevated breach risk or tight remaining SLA window requires supervisor awareness."
    else:
        esc_why = "No escalation triggered. SLA buffer is healthy and incident is within standard operating parameters."

    if esc_reasons:
        esc_reasons_html = "".join([f'<span class="factor-item">{r}</span>' for r in esc_reasons])
        esc_factors_html = f'<div style="margin-top:6px;"><span class="decision-label">Triggered Conditions:</span><br>{esc_reasons_html}</div>'
    else:
        esc_factors_html = ""

    sim_act_html = f'<div style="margin-top:6px; font-size:0.82rem; color:#94a3b8; font-style:italic;">{sim_action}</div>' if sim_action else ''

    trail_html = f"""
    <div style="margin-top: 10px; margin-bottom: 20px;">
        <!-- STEP 1: CATEGORY DETECTION -->
        <div class="decision-card" style="border-left: 4px solid #3b82f6;">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:#3b82f6;">1</span>
                    CATEGORY DETECTION
                </div>
                <div><span class="badge badge-blue">{cat}</span></div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="color:#60a5fa; font-weight:700; font-size:1.02rem;">✓ Category: {cat}</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:#3b82f6;">{cat_why}</div>
            </div>
            <div class="decision-section">
                {cat_evidence}
            </div>
        </div>

        <div class="connector-arrow">↓</div>

        <!-- STEP 2: PRIORITY ASSESSMENT -->
        <div class="decision-card" style="border-left: 4px solid #f59e0b;">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:#f59e0b;">2</span>
                    PRIORITY ASSESSMENT
                </div>
                <div>{get_priority_badge(pri)}</div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="font-weight:700; font-size:1.02rem;">✓ Priority: {get_priority_badge(pri)}</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:#f59e0b;">{pri_why}</div>
            </div>
            <div class="decision-section">
                {pri_evidence}
            </div>
        </div>

        <div class="connector-arrow">↓</div>

        <!-- STEP 3: SLA ASSIGNMENT -->
        <div class="decision-card" style="border-left: 4px solid #06b6d4;">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:#06b6d4;">3</span>
                    SLA ASSIGNMENT
                </div>
                <div><span class="badge badge-cyan">{resp_h}h / {res_h}h SLA</span></div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="color:#22d3ee; font-weight:700; font-size:1.02rem;">✓ Response SLA: {resp_h}h &nbsp;|&nbsp; Resolution SLA: {res_h}h</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:#06b6d4;">{sla_why}</div>
            </div>
            <div class="decision-section">
                {sla_evidence}
            </div>
        </div>

        <div class="connector-arrow">↓</div>

        <!-- STEP 4: INTELLIGENT ROUTING -->
        <div class="decision-card" style="border-left: 4px solid #8b5cf6;">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:#8b5cf6;">4</span>
                    INTELLIGENT ROUTING
                </div>
                <div><span class="badge badge-purple">{agent}</span></div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="color:#c084fc; font-weight:700; font-size:1.02rem;">✓ Assigned Agent: {agent}</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:#8b5cf6;">{routing_why}</div>
            </div>
            <div class="decision-section">
                {routing_evidence}
            </div>
        </div>

        <div class="connector-arrow">↓</div>

        <!-- STEP 5: BREACH RISK ASSESSMENT -->
        <div class="decision-card" style="border-left: 4px solid {risk_border};">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:{risk_border};">5</span>
                    BREACH RISK ASSESSMENT
                </div>
                <div>{get_risk_badge(risk_lvl)}</div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="font-weight:700; font-size:1.02rem;">✓ Breach Risk: {get_risk_badge(risk_lvl)} ({risk_pct}%)</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:{risk_border};">{risk_why}</div>
            </div>
            <div class="decision-section">
                {risk_evidence}
            </div>
        </div>

        <div class="connector-arrow">↓</div>

        <!-- STEP 6: HISTORICAL KNOWLEDGE MATCH -->
        <div class="decision-card" style="border-left: 4px solid #14b8a6;">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:#14b8a6;">6</span>
                    HISTORICAL KNOWLEDGE MATCH
                </div>
                <div><span class="badge badge-slate">TF-IDF Vector Match</span></div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="color:#2dd4bf; font-weight:700; font-size:1.02rem;">✓ Closest Reference Ticket Identified</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:#14b8a6;">{sim_why}</div>
            </div>
            <div class="decision-section">
                {sim_evidence}
            </div>
        </div>

        <div class="connector-arrow">↓</div>

        <!-- STEP 7: ESCALATION DECISION -->
        <div class="decision-card" style="border-left: 4px solid {esc_border};">
            <div class="decision-header">
                <div class="decision-step-title">
                    <span class="decision-step-num" style="background:{esc_border};">7</span>
                    ESCALATION DECISION
                </div>
                <div>{get_escalation_badge(esc_lvl)}</div>
            </div>
            <div class="decision-section">
                <span class="decision-label">Decision:</span><br>
                <span style="font-weight:700; font-size:1.02rem;">✓ Level: {get_escalation_badge(esc_lvl)}</span>
            </div>
            <div class="decision-section">
                <span class="decision-label">Why:</span>
                <div class="decision-why" style="border-left-color:{esc_border};">{esc_why}</div>
            </div>
            <div class="decision-section">
                {esc_factors_html}
                <div style="margin-top:8px;">
                    <span class="decision-label">Recommended Action:</span><br>
                    <div style="background:rgba(15,23,42,0.6); padding:8px 12px; border-radius:6px; font-size:0.88rem; color:#f8fafc; font-weight:600;">
                        👉 {esc_action}
                    </div>
                    {sim_act_html}
                </div>
            </div>
        </div>
    </div>
    """
    clean_markdown(trail_html)


def render_employee_ai_summary(ticket: dict) -> None:
    """
    Render safe, simplified explanation for employees without exposing internal operational mechanics.
    """
    cat = ticket.get("category", "General")
    pri = ticket.get("priority", "Medium")
    agent = ticket.get("assigned_agent", "IT Specialist")
    res_h = ticket.get("resolution_sla_hours", 24)
    kws = ticket.get("category_keywords", [])
    
    kws_note = f" (detected keywords: {', '.join(kws)})" if kws else ""

    clean_markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 10px; padding: 16px; margin-top: 10px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #60a5fa; margin-bottom: 12px; display:flex; align-items:center; gap:8px;">
            <span>🤖</span> Automated AI Triage & Resolution Policy
        </div>
        <ul style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.8; margin: 0; padding-left: 20px;">
            <li><strong>Category Detection:</strong> AI categorized your complaint as <span style="color:#60a5fa; font-weight:600;">{cat}</span>{kws_note}.</li>
            <li><strong>Priority Assessment:</strong> Priority was assigned as <span style="font-weight:600;">{pri}</span> based on urgency and user impact analysis.</li>
            <li><strong>Specialist Assignment:</strong> Your ticket has been assigned to an IT specialist (<strong style="color:#c084fc;">{agent}</strong>) with matching domain expertise.</li>
            <li><strong>SLA Target:</strong> Your target resolution time is <strong style="color:#34d399;">{res_h} hours</strong> in accordance with our IT Service Level Policy.</li>
        </ul>
    </div>
    """)


def render_ticket_chat(ticket: dict, viewer_role: str) -> None:
    """
    Render live ticket-specific communication channel between Employee and IT Agent.
    - Isolated per ticket ID.
    - Employee messages on right, Agent messages on left, System updates centered.
    - Real-time message submission with toasts and status preservation.
    """
    is_resolved = (ticket["status"] == "Resolved")
    
    # 1. Chat Header Card
    clean_markdown(f"""
    <div class="chat-header-card">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.3rem;">💬</span>
            <div>
                <strong style="color: #f8fafc; font-size: 1.02rem;">IT Support Conversation</strong><br>
                <span style="color: #94a3b8; font-size: 0.82rem;">Ticket: <code>{ticket['ticket_id']}</code> &nbsp;|&nbsp; Assigned: <strong style="color:#c084fc;">{ticket['assigned_agent']}</strong></span>
            </div>
        </div>
        <div>
            {get_status_badge(ticket['status'])}
        </div>
    </div>
    """)

    # 2. Conversation Messages Container
    messages = ticket.get("messages", [])
    chat_html = '<div class="chat-container">'
    if not messages:
        chat_html += """
        <div style="text-align:center; padding:32px 16px; color:#94a3b8;">
            <div style="font-size:1.9rem; margin-bottom:8px;">💬</div>
            <strong style="color:#cbd5e1; font-size:1.02rem;">No messages yet.</strong><br>
            <span style="font-size:0.86rem; color:#94a3b8;">Start a conversation with IT Support.</span>
        </div>
        """
    else:
        for msg in messages:
            sender = msg.get("sender", "System")
            ts_obj = msg.get("timestamp")
            if isinstance(ts_obj, datetime):
                ts = ts_obj.strftime("%I:%M %p")
            elif isinstance(ts_obj, str):
                ts = ts_obj
            else:
                ts = datetime.now().strftime("%I:%M %p")
            text_body = msg.get("message", "")
            
            if sender == "Employee":
                sender_label = "You (Employee)" if viewer_role == "employee" else "Employee"
                chat_html += f"""
                <div class="chat-msg-emp">
                    <div>{text_body}</div>
                    <span class="chat-meta">{sender_label} • {ts}</span>
                </div>
                """
            elif sender == "IT Agent":
                sender_label = f"IT Agent ({ticket['assigned_agent']})" if viewer_role == "employee" else f"You ({ticket['assigned_agent']})"
                chat_html += f"""
                <div class="chat-msg-agent">
                    <div>{text_body}</div>
                    <span class="chat-meta">{sender_label} • {ts}</span>
                </div>
                """
            else:
                chat_html += f"""
                <div class="chat-msg-sys">
                    ℹ️ {text_body} • <span style="opacity:0.75;">{ts}</span>
                </div>
                """
    chat_html += '</div>'
    clean_markdown(chat_html)

    # 3. Input Form or Resolution State Banner
    if is_resolved:
        clean_markdown("""
        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 12px 16px; text-align: center; color: #34d399; font-size: 0.88rem; margin-bottom: 15px;">
            ✓ <strong>Ticket Resolved</strong> — Conversation closed for new messages. All previous discussion records remain saved above.
        </div>
        """)
    else:
        if viewer_role == "employee":
            with st.form(f"emp_chat_form_{ticket['ticket_id']}"):
                emp_msg_input = st.text_input("Type your message...", placeholder="Type your message to IT Support...", key=f"emp_input_{ticket['ticket_id']}")
                send_btn = st.form_submit_button("📨 Send Message", type="primary", use_container_width=True)
            
            if send_btn and emp_msg_input.strip():
                if "messages" not in ticket:
                    ticket["messages"] = []
                ticket["messages"].append({
                    "sender": "Employee",
                    "message": emp_msg_input.strip(),
                    "timestamp": datetime.now()
                })
                st.toast("Message sent to IT Agent.", icon="📨")
                st.rerun()
        else:
            with st.form(f"agent_chat_form_{ticket['ticket_id']}"):
                agent_reply_input = st.text_input("Reply to Employee:", placeholder="Type support response or update to employee...", key=f"agent_input_{ticket['ticket_id']}")
                send_reply_btn = st.form_submit_button("📨 Send Reply", type="primary", use_container_width=True)
            
            if send_reply_btn and agent_reply_input.strip():
                if "messages" not in ticket:
                    ticket["messages"] = []
                ticket["messages"].append({
                    "sender": "IT Agent",
                    "message": agent_reply_input.strip(),
                    "timestamp": datetime.now()
                })
                st.toast("Reply sent to employee.", icon="📨")
                st.rerun()


# -------------------------------------------------------------
# Helper: End-to-End Automated Pipeline Execution
# -------------------------------------------------------------
def process_new_complaint(subject: str, description: str, affected_users: int = 1) -> dict:
    """
    Execute full 7-stage automated pipeline:
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
    matched_kws_raw = find_matched_keywords(ticket_text).get(pred_category, [])
    category_keywords = [format_keyword_name(k) for k in matched_kws_raw]
    category_why = "Matched keywords from subject/description." if category_keywords else "No domain keywords detected in text; assigned fallback general category."
    
    # 2. Prioritization
    priority_score, priority_reasons = calculate_priority_score(ticket_text, pred_category, affected_users)
    pred_priority = prioritize(ticket_text, pred_category, affected_users)
    pri_exp = explain_priority(ticket_text, pred_category, affected_users)
    if pred_priority == "Critical":
        priority_why = "High urgency signals + major organizational impact + multi-user scale."
    elif pred_priority == "High":
        priority_why = "Elevated urgency or significant operational impact detected."
    elif pred_priority == "Medium":
        priority_why = "Standard business urgency and moderate operational impact."
    else:
        priority_why = "Standard routine request with low urgency and single-user scope."
        
    # 3. SLA Deadlines
    sla_info = calculate_sla(created_time, pred_priority)
    sla_status, time_display, remaining_hours = get_sla_status(
        sla_info["resolution_deadline"],
        current_time=created_time
    )
    sla_exp = explain_sla(pred_priority)
    sla_policy = f"{pred_priority} priority follows the {pred_priority} SLA policy ({sla_info['response_sla_hours']}h response / {sla_info['resolution_sla_hours']}h resolution)."
    
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
    if risk_info["risk_level"] in ["CRITICAL", "HIGH"]:
        risk_why = "Risk is elevated because the ticket has high operational impact and limited SLA time."
    else:
        risk_why = "Risk is low/moderate because SLA resolution window is ample and agent load is manageable."
        
    # 6. Similar Ticket Retrieval
    similar_records = similarity_engine.find_similar_tickets(
        subject=subject,
        description=description,
        category=pred_category,
        top_n=3,
        threshold=0.15
    )
    sim_exp = similarity_engine.explain_similarity(similar_records, threshold=0.15)
    top_sim = similar_records[0] if similar_records else None
    
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
        "category_keywords": category_keywords,
        "category_why": category_why,
        "category_explanation": cat_exp,
        "priority": pred_priority,
        "priority_score": priority_score,
        "priority_reasons": priority_reasons,
        "priority_why": priority_why,
        "priority_explanation": pri_exp,
        "response_deadline": sla_info["response_deadline"],
        "resolution_deadline": sla_info["resolution_deadline"],
        "response_sla_hours": sla_info["response_sla_hours"],
        "resolution_sla_hours": sla_info["resolution_sla_hours"],
        "sla_status": sla_status,
        "time_display": time_display,
        "sla_policy": sla_policy,
        "sla_explanation": sla_exp,
        "assigned_agent": assignment_info["assigned_agent"],
        "agent_skills": assignment_info["skills"],
        "agent_previous_load": assignment_info["previous_load"],
        "agent_new_load": assignment_info["new_load"],
        "is_skill_matched": assignment_info["is_skill_matched"],
        "assignment_explanation": assignment_info["explanation"],
        "risk_percentage": risk_info["risk_percentage"],
        "risk_level": risk_info["risk_level"],
        "risk_reasons": risk_info["reasons"],
        "risk_why": risk_why,
        "risk_explanation": risk_info["explanation"],
        "similar_records": similar_records,
        "top_similar": top_sim,
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
        "messages": []
    }
    
    st.session_state["session_tickets"].insert(0, ticket_record)
    return ticket_record


# -------------------------------------------------------------
# SCREEN 1: LANDING / ROLE SELECTION
# -------------------------------------------------------------
def render_landing_screen():
    clean_markdown("""
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
    """)
    
    st.divider()
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        clean_markdown("""
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
        """)
        st.write("")
        if st.button("🚀 Enter Employee Portal", use_container_width=True, type="primary"):
            st.session_state["current_role"] = "employee"
            st.rerun()

    with col_right:
        clean_markdown("""
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
        """)
        st.write("")
        if st.button("🛡️ Enter IT Operations Center", use_container_width=True, type="secondary"):
            st.session_state["current_role"] = "agent"
            st.rerun()

    st.write("")
    st.divider()
    
    # System Status Section
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        clean_markdown("<div style='text-align:center; color:#94a3b8; font-size:0.9rem;'><span style='color:#10b981; font-weight:bold;'>●</span> <strong>AI Triage Engine:</strong> <span style='color:#34d399;'>Online</span></div>")
    with col_s2:
        clean_markdown("<div style='text-align:center; color:#94a3b8; font-size:0.9rem;'><span style='color:#10b981; font-weight:bold;'>●</span> <strong>SLA Monitoring:</strong> <span style='color:#34d399;'>Active</span></div>")
    with col_s3:
        clean_markdown("<div style='text-align:center; color:#94a3b8; font-size:0.9rem;'><span style='color:#60a5fa; font-weight:bold;'>●</span> <strong>Ticket Intelligence:</strong> <span style='color:#60a5fa;'>Ready (1,000 Tickets)</span></div>")


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
        clean_markdown(f"""
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
        """)

        st.divider()

        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📋 Recent Complaints")
            if not session_tickets:
                st.info("No complaints submitted yet. Submit a new IT support request to get started.")
            else:
                headers = ["Ticket ID", "Issue", "Category", "Priority", "Status", "Agent", "SLA Status"]
                rows = [
                    [
                        f"<strong style='color:#60a5fa;'>{t['ticket_id']}</strong>",
                        t['subject'],
                        f"<span class='badge badge-slate'>{t['category']}</span>",
                        get_priority_badge(t['priority']),
                        get_status_badge(t['status']),
                        f"<span style='color:#cbd5e1;'>{t['assigned_agent']}</span>",
                        get_sla_badge(t['sla_status'])
                    ]
                    for t in session_tickets[:5]
                ]
                render_custom_table(headers, rows)

        with col_right:
            st.subheader("⚡ Quick Help")
            clean_markdown("""
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
            """)

    # ---------------------------------------------------------
    # VIEW 2: New Complaint (Clean Real Form)
    # ---------------------------------------------------------
    elif emp_nav == "➕ New Complaint":
        st.header("➕ Submit New IT Complaint")
        st.caption("Provide issue details. Our automated triage engine will categorize, prioritize, and assign your ticket immediately.")

        with st.form("employee_complaint_form"):
            new_subject = st.text_input("Issue Title:", placeholder="e.g. VPN not connecting, Excel crashing, Printer offline...")
            col_u1, _ = st.columns([1, 2])
            with col_u1:
                new_users = st.number_input("Affected Users:", min_value=1, value=1, step=1)
            new_desc = st.text_area("Description:", height=130, placeholder="Describe symptoms, error codes, and what you were trying to do...")
            submit_btn = st.form_submit_button("Submit Complaint", type="primary", use_container_width=True)

        if submit_btn:
            if not new_subject.strip() or not new_desc.strip():
                st.error("Please provide both an Issue Title and Description for your complaint.")
            else:
                record = process_new_complaint(new_subject, new_desc, new_users)
                
                # Professional Pop-up / Toast Alerts
                st.toast("Complaint submitted successfully", icon="✅")
                st.toast(f"Ticket #{record['ticket_id']} created and sent for AI triage.", icon="🤖")
                st.toast(f"Ticket #{record['ticket_id']} assigned to {record['assigned_agent']}.", icon="🧑‍💼")
                if record["escalation_status"] != "NO ESCALATION":
                    st.toast(f"Ticket #{record['ticket_id']} has been escalated for immediate attention.", icon="🚨")
                if "AT RISK" in record["sla_status"]:
                    st.toast(f"Warning: Ticket #{record['ticket_id']} is approaching its SLA deadline.", icon="⚠️")
                
                # Post-submission confirmation card (Employee-Facing)
                clean_markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 12px; padding: 22px; margin-top: 15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(51,65,85,0.6); padding-bottom:12px; margin-bottom:14px;">
                        <div>
                            <span style="font-size:1.3rem; font-weight:700; color:#60a5fa;">AI TRIAGE COMPLETE ✓</span>
                            <span style="margin-left:8px; font-family:monospace; color:#cbd5e1; font-size:1.05rem;">({record['ticket_id']})</span>
                        </div>
                        <div>
                            {get_sla_badge(record['sla_status'])}
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 14px; margin: 15px 0;">
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Category:</span><br><strong>{record['category']}</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Priority:</span><br>{get_priority_badge(record['priority'])}</div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Assigned Agent:</span><br><strong>{record['assigned_agent']}</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Response SLA:</span><br><strong>{record['response_sla_hours']} Hours</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Resolution SLA:</span><br><strong>{record['resolution_sla_hours']} Hours</strong></div>
                        <div><span style="color:#94a3b8; font-size:0.8rem;">Current Status:</span><br>{get_status_badge(record['status'])}</div>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; font-size: 0.9rem; color: #cbd5e1;">
                        ⏱️ <strong>Resolution Deadline:</strong> <code>{record['resolution_deadline'].strftime('%d %b %Y, %I:%M %p')}</code> ({record['sla_status']})
                    </div>
                </div>
                """)

                with st.expander("💡 How did AI decide?", expanded=True):
                    render_employee_ai_summary(record)

    # ---------------------------------------------------------
    # VIEW 3: My Complaints & Live Chat with IT Agent
    # ---------------------------------------------------------
    elif emp_nav == "📋 My Complaints":
        st.header("📋 My Complaints")
        st.caption("Inspect complaint progress, monitor resolution deadlines, and communicate in real time with your assigned IT technician.")

        if not session_tickets:
            st.info("No complaints submitted yet. Use **New Complaint** to submit a support request.")
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

            headers = ["Ticket ID", "Issue", "Category", "Priority", "Status", "Assigned Agent", "SLA Status"]
            rows = [
                [
                    f"<strong style='color:#60a5fa;'>{t['ticket_id']}</strong>",
                    t['subject'],
                    f"<span class='badge badge-slate'>{t['category']}</span>",
                    get_priority_badge(t['priority']),
                    get_status_badge(t['status']),
                    f"<span style='color:#cbd5e1;'>{t['assigned_agent']}</span>",
                    get_sla_badge(t['sla_status'])
                ]
                for t in filtered_list
            ]
            render_custom_table(headers, rows)

            st.divider()

            # Ticket Details & Chat
            st.subheader("📄 Ticket Details")
            ticket_options = [t["ticket_id"] + " - " + t["subject"] for t in session_tickets]
            selected_ticket_str = st.selectbox("Select Ticket to View Details & Conversation:", ticket_options)
            
            selected_id = selected_ticket_str.split(" - ")[0]
            selected_ticket = next((t for t in session_tickets if t["ticket_id"] == selected_id), None)

            if selected_ticket:
                # Ticket summary card
                clean_markdown(f"""
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
                """)

                with st.expander("💡 How did AI decide this ticket?", expanded=False):
                    render_employee_ai_summary(selected_ticket)

                if selected_ticket["status"] == "Resolved":
                    st.success(
                        f"✅ **Resolved successfully on:** `{selected_ticket['resolved_at'].strftime('%d %b %Y, %I:%M %p')}` | "
                        f"**Resolution Time:** `{selected_ticket['resolution_hours']:.1f} hrs` | "
                        f"**SLA Result:** `{selected_ticket['sla_result']}`"
                    )

                st.divider()

                # Communication with IT Support
                st.subheader(f"💬 Communication with IT Support — {selected_ticket['ticket_id']}")
                st.caption("Communicate directly with your assigned technician in real time.")
                render_ticket_chat(selected_ticket, viewer_role="employee")

    # ---------------------------------------------------------
    # VIEW 4: Complaint Report
    # ---------------------------------------------------------
    elif emp_nav == "📄 Complaint Report":
        st.header("📄 Complaint Report")
        st.caption("Official incident summary report and record documentation.")

        if not session_tickets:
            st.info("No complaints submitted yet. Use **New Complaint** to submit a support request.")
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

                clean_markdown(f"""
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
                """)

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
    
    # LIVE OPERATIONS Counts (Derived purely from session_tickets)
    sess_total = len(session_tickets)
    sess_open = sum(1 for t in session_tickets if t["status"] == "Open")
    sess_prog = sum(1 for t in session_tickets if t["status"] == "In Progress")
    sess_res = sum(1 for t in session_tickets if t["status"] == "Resolved")
    sess_breached = sum(1 for t in session_tickets if "BREACHED" in t["sla_status"])
    sess_at_risk = sum(1 for t in session_tickets if "AT RISK" in t["sla_status"])
    sess_high_risk = sum(1 for t in session_tickets if t["risk_level"] in ["HIGH", "CRITICAL"])
    
    live_met = sess_total - sess_breached
    live_compliance = ((live_met / sess_total) * 100.0) if sess_total > 0 else 100.0

    # ---------------------------------------------------------
    # VIEW 1: Operations Overview
    # ---------------------------------------------------------
    if agent_nav == "📊 Operations Overview":
        # Header with live status badge
        clean_markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div>
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700;">IT Operations Center</h1>
                <p style="color: #94a3b8; margin: 4px 0 0 0;">Real-time service health, proactive SLA monitoring, and automated incident triage</p>
            </div>
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; color: #34d399; font-weight: 600;">
                ● All systems operational
            </div>
        </div>
        """)

        st.divider()

        # LIVE OPERATIONS Top KPI Cards Grid
        clean_markdown(f"""
        <div style="margin-bottom: 8px; font-weight: 700; color: #60a5fa; font-size: 0.95rem; letter-spacing: 0.5px;">
            LIVE OPERATIONS (SESSION)
        </div>
        <div class="kpi-grid">
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">TOTAL LIVE TICKETS</div>
                <div class="kpi-value">{sess_total}</div>
                <div class="kpi-sub">Current session</div>
            </div>
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">OPEN</div>
                <div class="kpi-value" style="color:#60a5fa;">{sess_open}</div>
                <div class="kpi-sub">Awaiting pick-up</div>
            </div>
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">IN PROGRESS</div>
                <div class="kpi-value" style="color:#fbbf24;">{sess_prog}</div>
                <div class="kpi-sub">Active in queue</div>
            </div>
            <div class="kpi-card kpi-green">
                <div class="kpi-title">RESOLVED</div>
                <div class="kpi-value" style="color:#34d399;">{sess_res}</div>
                <div class="kpi-sub">Closed successfully</div>
            </div>
            <div class="kpi-card kpi-red">
                <div class="kpi-title">SLA BREACHED</div>
                <div class="kpi-value" style="color:#f87171;">{sess_breached}</div>
                <div class="kpi-sub">Missed target SLA</div>
            </div>
            <div class="kpi-card kpi-amber">
                <div class="kpi-title">AT RISK</div>
                <div class="kpi-value" style="color:#fbbf24;">{sess_at_risk}</div>
                <div class="kpi-sub">Approaching deadline</div>
            </div>
            <div class="kpi-card kpi-green" style="background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.5);">
                <div class="kpi-title" style="color:#34d399;">LIVE SLA COMPLIANCE</div>
                <div class="kpi-value" style="color:#34d399;">{live_compliance:.1f}%</div>
                <div class="kpi-sub" style="color:#a7f3d0;">Live session health</div>
            </div>
            <div class="kpi-card kpi-purple">
                <div class="kpi-title">HIGH/CRITICAL RISK</div>
                <div class="kpi-value" style="color:#c084fc;">{sess_high_risk}</div>
                <div class="kpi-sub">Requiring supervision</div>
            </div>
        </div>
        """)

        st.divider()

        # ⏱️ SLA Monitoring Section
        st.subheader("⏱️ SLA Monitoring")
        col_sla1, col_sla2, col_sla3, col_sla4 = st.columns(4)
        with col_sla1:
            st.metric("Live SLA Compliance", f"{live_compliance:.1f}%", delta="Normal Health")
        with col_sla2:
            st.metric("Live SLA Met", sess_res if sess_breached == 0 else max(0, sess_res - sess_breached))
        with col_sla3:
            st.metric("Live SLA Breached", sess_breached)
        with col_sla4:
            st.metric("Live Session At Risk", sess_at_risk)

        st.write("")

        # Live session stream
        if not session_tickets:
            st.info("No active tickets in current session. Once an employee submits a complaint, live triage tracking will appear here.")
        else:
            st.markdown(f"##### ⚡ Live Incoming Triage Activity ({len(session_tickets)} Session Tickets)")
            headers = ["Ticket ID", "Subject", "Category", "Priority", "Agent", "Breach Risk", "Escalation", "SLA Status"]
            rows = [
                [
                    f"<strong style='color:#60a5fa;'>{t['ticket_id']}</strong>",
                    t['subject'],
                    f"<span class='badge badge-slate'>{t['category']}</span>",
                    get_priority_badge(t['priority']),
                    f"<span style='color:#cbd5e1;'>{t['assigned_agent']}</span>",
                    f"{get_risk_badge(t['risk_level'])} ({t['risk_percentage']}%)",
                    get_escalation_badge(t['escalation_level']),
                    get_sla_badge(t['sla_status'])
                ]
                for t in session_tickets[:5]
            ]
            render_custom_table(headers, rows)
            st.divider()

        # Operational Analytics Grid (Historical Baseline Knowledge)
        st.markdown("<h4 style='color:#c084fc; margin-top:20px;'>📊 Historical Knowledge Base Analytics (1,000 Tickets)</h4>", unsafe_allow_html=True)
        
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
            st.markdown("##### SLA Met vs Breached (Historical)")
            hist_breached = int((df_historical["sla_breached"] == True).sum())
            hist_met = len(df_historical) - hist_breached
            sla_dist = pd.Series({
                "SLA Met": hist_met,
                "SLA Breached": hist_breached
            })
            st.bar_chart(sla_dist)

    # ---------------------------------------------------------
    # VIEW 2: Active Tickets Queue & AI Decision Trail
    # ---------------------------------------------------------
    elif agent_nav == "🎫 Active Tickets":
        st.header("🎫 Active Tickets")
        st.caption("Manage live queue operations, inspect transparent 🧠 AI Decision Trails, and update ticket statuses.")

        if not session_tickets:
            st.info("No active tickets.")
        else:
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
                headers = ["Ticket ID", "Subject", "Category", "Priority", "Status", "Assigned Agent", "SLA Status", "Risk", "Created"]
                rows = [
                    [
                        f"<strong style='color:#60a5fa;'>{t['ticket_id']}</strong>",
                        t['subject'],
                        f"<span class='badge badge-slate'>{t['category']}</span>",
                        get_priority_badge(t['priority']),
                        get_status_badge(t['status']),
                        f"<span style='color:#cbd5e1;'>{t['assigned_agent']}</span>",
                        get_sla_badge(t['sla_status']),
                        f"{get_risk_badge(t['risk_level'])} ({t['risk_percentage']}%)",
                        f"<span style='color:#94a3b8;'>{t['created_at'].strftime('%I:%M %p')}</span>"
                    ]
                    for t in sess_filtered
                ]
                render_custom_table(headers, rows)
            else:
                st.info("No active tickets matching current filters.")

            st.divider()

            # Operational Ticket Inspector & Customer Communication
            st.subheader("🔍 Operational Ticket Inspector")
            t_opts = [t["ticket_id"] + " - " + t["subject"] for t in session_tickets]
            inspected_str = st.selectbox("Select Session Ticket to Inspect & Manage:", t_opts)
            inspected_id = inspected_str.split(" - ")[0]
            inspected_t = next((t for t in session_tickets if t["ticket_id"] == inspected_id), None)

            if inspected_t:
                # Top Overview Card
                clean_markdown(f"""
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
                """)

                # 1. AI DECISION TRAIL (EXPANDABLE TIMELINE)
                with st.expander("🧠 AI Decision Trail (Step-by-Step Explainability)", expanded=True):
                    st.caption("Transparent, multi-factor reasoning across all 7 stages of the automated IT incident pipeline.")
                    render_ai_decision_trail(inspected_t)

                st.divider()

                # 2. EMPLOYEE COMMUNICATION CHANNEL
                st.markdown("#### 💬 Employee Communication")
                st.caption(f"Direct communication thread with employee for Ticket {inspected_t['ticket_id']}.")
                render_ticket_chat(inspected_t, viewer_role="agent")

                st.divider()

                # 3. STATUS MANAGEMENT
                st.markdown("#### ⚙️ Status Management")
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
                                
                                if "messages" not in inspected_t:
                                    inspected_t["messages"] = []
                                inspected_t["messages"].append({
                                    "sender": "System",
                                    "message": f"Ticket marked as Resolved by IT Agent ({inspected_t['assigned_agent']}). Outcome: {inspected_t['sla_result']} (Resolution Time: {res_h:.1f} hrs).",
                                    "timestamp": resolved_time
                                })
                                st.toast(f"Ticket #{inspected_t['ticket_id']} resolved successfully.", icon="✅")
                            else:
                                if "messages" not in inspected_t:
                                    inspected_t["messages"] = []
                                inspected_t["messages"].append({
                                    "sender": "System",
                                    "message": f"Ticket status updated to '{new_status_val}' by IT Agent ({inspected_t['assigned_agent']}).",
                                    "timestamp": datetime.now()
                                })
                                st.toast(f"Ticket #{inspected_t['ticket_id']} moved to {new_status_val}.", icon="🔄")
                            st.rerun()

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
                clean_markdown("""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 20px; margin: 10px 0;">
                    <h4 style="color: #34d399; margin: 0 0 6px 0;">✓ No active escalations</h4>
                    <p style="color: #94a3b8; margin: 0;">All monitored live tickets are currently within their escalation thresholds.</p>
                </div>
                """)
            else:
                for esc_t in live_escalations:
                    level = esc_t["escalation_level"]
                    is_critical = (level == "CRITICAL ESCALATION")
                    border_color = "#ef4444" if is_critical else "#f59e0b"
                    bg_color = "rgba(239, 68, 68, 0.1)" if is_critical else "rgba(245, 158, 11, 0.1)"
                    
                    clean_markdown(f"""
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
                    """)

        # TAB 2: Historical SLA Alerts
        with tab_hist_esc:
            st.subheader("Historical SLA Alerts (tickets.csv)")
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
                if load >= 5:
                    status_badge = '<span class="badge badge-red">HIGH WORKLOAD</span>'
                    card_border = "#ef4444"
                elif load >= 2:
                    status_badge = '<span class="badge badge-amber">MODERATE WORKLOAD</span>'
                    card_border = "#f59e0b"
                else:
                    status_badge = '<span class="badge badge-green">LOW WORKLOAD</span>'
                    card_border = "#10b981"

                clean_markdown(f"""
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
                """)

            if st.button("🔄 Reset Agent Workloads to 0", use_container_width=True):
                st.session_state["agent_pool"] = get_fresh_session_agents()
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
        st.caption("Comprehensive historical operational insights from 1,000 reference records.")

        # KPI Metrics from Historical Base
        hist_total = len(df_historical)
        hist_breached = int((df_historical["sla_breached"] == True).sum())
        hist_met = hist_total - hist_breached
        hist_compliance = (hist_met / hist_total * 100.0) if hist_total > 0 else 100.0
        avg_res_h = float(df_historical["resolution_hours"].mean()) if "resolution_hours" in df_historical.columns else 0.0
        breach_pct = float((df_historical["sla_breached"] == True).mean()) * 100.0 if "sla_breached" in df_historical.columns else 0.0

        clean_markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">TOTAL HISTORICAL TICKETS</div>
                <div class="kpi-value">{hist_total:,}</div>
                <div class="kpi-sub">Reference knowledge base</div>
            </div>
            <div class="kpi-card kpi-green">
                <div class="kpi-title">HISTORICAL SLA COMPLIANCE</div>
                <div class="kpi-value" style="color:#34d399;">{hist_compliance:.1f}%</div>
                <div class="kpi-sub">{hist_met:,} Met vs {hist_breached:,} Breached</div>
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
        """)

        st.divider()

        # Detailed Charts
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.subheader("Category Distribution (Historical)")
            st.bar_chart(df_historical["category"].value_counts())
        with col_an2:
            st.subheader("Priority Distribution (Historical)")
            st.bar_chart(df_historical["priority"].value_counts())

        col_an3, col_an4 = st.columns(2)
        with col_an3:
            st.subheader("Ticket Status Distribution (Historical)")
            st.bar_chart(df_historical["status"].value_counts())
        with col_an4:
            st.subheader("SLA Met vs Breached (Historical)")
            sla_dist = pd.Series({
                "SLA Met": hist_met,
                "SLA Breached": hist_breached
            })
            st.bar_chart(sla_dist)

        st.divider()
        col_an5, col_an6 = st.columns(2)
        with col_an5:
            st.subheader("Active Session Agent Workload")
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
