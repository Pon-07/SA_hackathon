from typing import Any, Dict, List, Optional

# User Directory with Generic Role Accounts (No Personal Names)
USERS: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # EMPLOYEE (End-user submitting IT complaints)
    # -------------------------------------------------------------
    "employee": {
        "username": "employee",
        "password": "password123",
        "name": "Employee",
        "role": "employee",
        "role_title": "Employee",
        "department": "Enterprise Staff",
        "avatar": "👤",
        "email": "employee@company.internal",
        "badge_color": "#3b82f6"
    },
    # Backward compatibility alias
    "emp_sarah": {
        "username": "employee",
        "password": "password123",
        "name": "Employee",
        "role": "employee",
        "role_title": "Employee",
        "department": "Enterprise Staff",
        "avatar": "👤",
        "email": "employee@company.internal",
        "badge_color": "#3b82f6"
    },
    "emp_alex": {
        "username": "employee",
        "password": "password123",
        "name": "Employee",
        "role": "employee",
        "role_title": "Employee",
        "department": "Enterprise Staff",
        "avatar": "👤",
        "email": "employee@company.internal",
        "badge_color": "#3b82f6"
    },
    "emp_david": {
        "username": "employee",
        "password": "password123",
        "name": "Employee",
        "role": "employee",
        "role_title": "Employee",
        "department": "Enterprise Staff",
        "avatar": "👤",
        "email": "employee@company.internal",
        "badge_color": "#3b82f6"
    },

    # -------------------------------------------------------------
    # SPECIALIST (IT Support Technician handling assigned queues)
    # -------------------------------------------------------------
    "specialist": {
        "username": "specialist",
        "password": "password123",
        "name": "Specialist",
        "agent_name": "Specialist",
        "role": "agent",
        "role_title": "Specialist",
        "department": "IT Operations",
        "avatar": "🛡️",
        "email": "specialist@it.company.internal",
        "skills": ["Network", "Security", "Hardware", "Software", "Access/Account", "Email", "Printer"],
        "badge_color": "#8b5cf6"
    },
    # Backward compatibility alias
    "agent": {
        "username": "specialist",
        "password": "password123",
        "name": "Specialist",
        "agent_name": "Specialist",
        "role": "agent",
        "role_title": "Specialist",
        "department": "IT Operations",
        "avatar": "🛡️",
        "email": "specialist@it.company.internal",
        "skills": ["Network", "Security", "Hardware", "Software", "Access/Account", "Email", "Printer"],
        "badge_color": "#8b5cf6"
    },
    "agent_priya": {
        "username": "specialist",
        "password": "password123",
        "name": "Specialist",
        "agent_name": "Specialist",
        "role": "agent",
        "role_title": "Specialist",
        "department": "IT Operations",
        "avatar": "🛡️",
        "email": "specialist@it.company.internal",
        "skills": ["Network", "Security"],
        "badge_color": "#8b5cf6"
    },
    "agent_marcus": {
        "username": "specialist",
        "password": "password123",
        "name": "Specialist",
        "agent_name": "Specialist",
        "role": "agent",
        "role_title": "Specialist",
        "department": "IT Operations",
        "avatar": "🛡️",
        "email": "specialist@it.company.internal",
        "skills": ["Hardware", "Printer"],
        "badge_color": "#8b5cf6"
    },
    "agent_elena": {
        "username": "specialist",
        "password": "password123",
        "name": "Specialist",
        "agent_name": "Specialist",
        "role": "agent",
        "role_title": "Specialist",
        "department": "IT Operations",
        "avatar": "🛡️",
        "email": "specialist@it.company.internal",
        "skills": ["Software", "Access/Account", "Email"],
        "badge_color": "#8b5cf6"
    },

    # -------------------------------------------------------------
    # OPERATIONS ADMIN (Full System Authority)
    # -------------------------------------------------------------
    "admin": {
        "username": "admin",
        "password": "admin123",
        "name": "Operations Admin",
        "role": "admin",
        "role_title": "Operations Admin",
        "department": "IT Operations Management",
        "avatar": "👑",
        "email": "admin@it.company.internal",
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


def is_employee(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("role") == "employee")


def is_agent(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("role") in ["agent", "admin"])


def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and user.get("role") == "admin")
