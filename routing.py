import copy
from typing import List, Dict, Any, Tuple

DEFAULT_AGENTS: List[Dict[str, Any]] = [
    {
        "name": "Agent_01",
        "skills": ["Network", "Security"],
        "load": 3
    },
    {
        "name": "Agent_02",
        "skills": ["Hardware", "Printer"],
        "load": 5
    },
    {
        "name": "Agent_03",
        "skills": ["Software", "Email"],
        "load": 2
    },
    {
        "name": "Agent_04",
        "skills": ["Access/Account", "Security"],
        "load": 4
    },
    {
        "name": "Agent_05",
        "skills": ["Network", "Software"],
        "load": 1
    }
]

def get_initial_agents() -> List[Dict[str, Any]]:
    """Return a fresh copy of the default agent configuration."""
    return copy.deepcopy(DEFAULT_AGENTS)

def assign_ticket(category: str, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligently assign a ticket to the best-suited agent:
    1. Filter agents with matching skill for the category.
    2. Pick the matching agent with the lowest current workload.
    3. If no skill match, fallback to the overall least-loaded agent.
    4. Increment the selected agent's workload.
    """
    if not agents:
        raise ValueError("Agent list cannot be empty")

    # 1. Filter by category skill match
    matching_agents = [a for a in agents if category in a.get("skills", [])]

    if matching_agents:
        # Select matching agent with lowest workload (tie-break by list order)
        selected_agent = min(matching_agents, key=lambda a: a["load"])
        is_skill_matched = True
    else:
        # Fallback to least-loaded agent overall
        selected_agent = min(agents, key=lambda a: a["load"])
        is_skill_matched = False

    previous_load = selected_agent["load"]
    selected_agent["load"] += 1
    new_load = selected_agent["load"]

    explanation = explain_assignment(
        category=category,
        assigned_agent=selected_agent["name"],
        skills=selected_agent.get("skills", []),
        previous_load=previous_load,
        is_skill_matched=is_skill_matched
    )

    return {
        "assigned_agent": selected_agent["name"],
        "skills": selected_agent.get("skills", []),
        "previous_load": previous_load,
        "new_load": new_load,
        "is_skill_matched": is_skill_matched,
        "explanation": explanation
    }

def explain_assignment(
    category: str,
    assigned_agent: str,
    skills: List[str],
    previous_load: int,
    is_skill_matched: bool
) -> str:
    """Generate human-readable assignment explainability string."""
    skills_str = ", ".join(skills)
    if is_skill_matched:
        return (
            f"Assigned to {assigned_agent} because they have {category} expertise "
            f"({skills_str}) and the lowest current workload ({previous_load} ticket{'s' if previous_load != 1 else ''}) "
            f"among eligible agents."
        )
    else:
        return (
            f"No exact skill match found for category '{category}'. "
            f"Assigned to {assigned_agent} as the least-loaded available agent "
            f"({previous_load} ticket{'s' if previous_load != 1 else ''})."
        )
