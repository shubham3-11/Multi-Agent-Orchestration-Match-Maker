# Sample dataset of user profiles for matchmaking
SAMPLE_USERS = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Charlie", "age": 25},
    {"name": "Diana", "age": 30},
    {"name": "Ethan", "age": 40},
    {"name": "Fiona", "age": 27},
    {"name": "George", "age": 27},
    {"name": "Hannah", "age": 30},
    {"name": "Ian", "age": 25},
    {"name": "Jane", "age": 40}
]

def find_matches(current_age: int) -> dict:
    """Find profiles from SAMPLE_USERS that have the same age as the current user."""
    matches = [user for user in SAMPLE_USERS if user.get("age") == current_age]
    return {"status": "success", "matches": matches}
