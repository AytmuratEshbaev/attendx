"""Role-based permission system with hierarchy."""

from enum import StrEnum


class Role(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TEACHER = "teacher"
    API = "api"


ROLE_HIERARCHY: dict[str, int] = {
    Role.SUPER_ADMIN: 100,
    Role.ADMIN: 75,
    Role.TEACHER: 50,
    Role.API: 25,
    # Legacy aliases
    "superadmin": 100,
}


def has_permission(user_role: str, required_role: str) -> bool:
    """Check if user_role meets or exceeds the required_role level."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level
