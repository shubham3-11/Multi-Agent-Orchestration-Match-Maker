# filepath: agents/tools/memory_tools.py
# Simple in-memory profile store
PROFILE_DB: dict[str, dict] = {}

def store_profile(user_id: str, name: str = "", age: int = -1) -> dict:
    """
    Store or update the user's profile information.
    - name: pass empty string "" if not updating the name.
    - age: pass -1 if not updating the age.
    Returns: {"status": "success", "stored_profile": {...}}
    """
    profile = PROFILE_DB.get(user_id, {}).copy()
    if isinstance(name, str) and name != "":
        profile["name"] = name
    if isinstance(age, int) and age >= 0:
        profile["age"] = age
    PROFILE_DB[user_id] = profile
    return {"status": "success", "stored_profile": profile}

def load_profile(user_id: str) -> dict:
    """
    Load the user's profile information if it exists.
    Returns: {"status": "success" | "not_found", "profile": {...} | {}}
    """
    profile = PROFILE_DB.get(user_id)
    if profile is None:
        return {"status": "not_found", "profile": {}}
    return {"status": "success", "profile": profile}
