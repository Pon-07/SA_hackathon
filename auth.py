from typing import Any, Dict, List, Optional

# User Directory with Predefined Hackathon Test Accounts
USERS: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # EMPLOYEES (End-users submitting IT complaints)
    # -------------------------------------------------------------
    "emp_sarah": {
        "username": "emp_sarah",
        "password": "password123",
        "name": "Sarah Jenkins",
        "role": "employee",
        "role_title": "Senior Software Engineer",
        "department": "Engineering & Cloud Platform",
        "avatar": "👩‍💻",
        "email": "sarah.jenkins@company.internal",
        "badge_color": "#3b82f6"
    },
    "emp_alex": {
        "username": "emp_alex",
        "password": "password123",
        "name": "Alex Rivera",
        "role": "employee",
        "role_title": "Product Marketing Lead",
        "department": "Growth & Communications",
        "avatar": "👨‍💼",
        "email": "alex.rivera@company.internal",
        "badge_color": "#3b82f6"
    },
    "emp_david": {
        "username": "emp_david",
        "password": "password123",
        "name": "David Chen",
        "role": "employee",
        "role_title": "Senior Financial Analyst",
        "department": "Finance & Analytics",
        "avatar": "🧑‍💻",
        "email": "david.chen@company.internal",
        "badge_color": "#3b82f6"
    },
    "employee": {
        "username": "employee",
        "password": "password123",
        "name": "Jordan Lee",
        "role": "employee",
        "role_title": "Operations Specialist",
        "department": "General Business Operations",
        "avatar": "👤",
        "email": "jordan.lee@company.internal",
        "badge_color": "#3b82f6"
    },

    # -------------------------------------------------------------
    # IT SUPPORT SPECIALISTS (Technicians handling assigned queues)
    # -------------------------------------------------------------
    "agent_priya": {
        "username": "agent_priya",
        "password": "password123",
        "name": "Priya Sharma",
        "agent_name": "Priya Sharma",
        "role": "agent",
        "role_title": "L2 Network & Security Specialist",
        "department": "IT Infrastructure & Security",
        "avatar": "🛡️",
        "email": "priya.sharma@it.company.internal",
        "skills": ["Network", "Security"],
        "badge_color": "#8b5cf6"
    },
    "agent_marcus": {
        "username": "agent_marcus",
        "password": "password123",
        "name": "Marcus Vance",
        "agent_name": "Marcus Vance",
        "role": "agent",
        "role_title": "Hardware & Peripherals Engineer",
        "department": "End-User Computing",
        "avatar": "💻",
        "email": "marcus.vance@it.company.internal",
        "skills": ["Hardware", "Printer"],
        "badge_color": "#8b5cf6"
    },
    "agent_elena": {
        "username": "agent_elena",
        "password": "password123",
        "name": "Elena Rostova",
        "agent_name": "Elena Rostova",
        "role": "agent",
        "role_title": "Enterprise Applications Lead",
        "department": "Business Applications & IAM",
        "avatar": "🔧",
        "email": "elena.rostova@it.company.internal",
        "skills": ["Software", "Access/Account", "Email"],
        "badge_color": "#8b5cf6"
    },
    "agent": {
        "username": "agent",
        "password": "password123",
        "name": "Alex Morgan",
        "agent_name": "Agent_01",
        "role": "agent",
        "role_title": "IT Support Technician",
        "department": "IT Service Desk",
        "avatar": "🧑‍🔧",
        "email": "alex.morgan@it.company.internal",
        "skills": ["Network", "Hardware", "Software"],
        "badge_color": "#8b5cf6"
    },

    # -------------------------------------------------------------
    # IT OPERATIONS DIRECTORS / AUDITORS (Full System Authority)
    # -------------------------------------------------------------
    "admin": {
        "username": "admin",
        "password": "admin123",
        "name": "Alex Mercer",
        "role": "admin",
        "role_title": "Director of IT Operations & Infrastructure",
        "department": "Global IT Command & SLA Compliance",
        "avatar": "👑",
        "email": "alex.mercer@director.company.internal",
        "skills": ["All"],
        "badge_color": "#ec4899"
    }
}


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Validate credentials against user store. Returns user dict on success, None on failure.
    """
    if not username or not password:
        return None
    user = USERS.get(username.strip().lower())
    if user and user["password"] == password:
        # Return safe profile copy (omit raw password)
        profile = dict(user)
        profile.pop("password", None)
        return profile
    return None


def get_user_profile(username: str) -> Optional[Dict[str, Any]]:
    """Retrieve user metadata by username."""
    user = USERS.get(username.strip().lower())
    if user:
        profile = dict(user)
        profile.pop("password", None)
        return profile
    return None


def get_demo_presets() -> List[Dict[str, Any]]:
    """
    Return quick-login presets for hackathon judges and evaluators.
    """
    return [
        {
            "id": "emp_sarah",
            "label": "👩‍💻 Login as Employee (Sarah Jenkins)",
            "role": "Employee Portal",
            "desc": "File complaints, track SLA countdown, chat with assigned IT technician",
            "username": "emp_sarah",
            "password": "password123"
        },
        {
            "id": "agent_priya",
            "label": "🛡️ Login as IT Specialist (Priya Sharma)",
            "role": "IT Specialist",
            "desc": "Inspect assigned Network/Security queue, review AI Decision Trail, resolve tickets",
            "username": "agent_priya",
            "password": "password123"
        },
        {
            "id": "admin",
            "label": "👑 Login as Operations Admin (Alex Mercer)",
            "role": "IT Operations Admin",
            "desc": "Global SLA oversight, live escalations, agent workload balancing & Explainable AI Hub",
            "username": "admin",
            "password": "admin123"
        }
    ]


def is_employee(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("role") == "employee")


def is_agent(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("role") in ["agent", "admin"])


def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("role") == "admin")
