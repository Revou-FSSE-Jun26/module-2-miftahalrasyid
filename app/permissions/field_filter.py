from app.permissions import FIELD_PERMISSIONS


def get_allowed_fields(table: str, roles: list, operation: str) -> set:
    """
    Get the union of allowed fields across all of the user's roles.
    Higher-privilege roles grant more fields.
    """
    allowed = set()
    for role in roles:
        role_perms = FIELD_PERMISSIONS.get(table, {}).get(role, {})
        fields = role_perms.get(operation, set())
        if isinstance(fields, set):
            allowed |= fields
    return allowed


def get_delete_policy(table: str, roles: list) -> str | None:
    """
    Returns the highest delete privilege across user's roles.
    Priority: "hard" > "soft" > None
    """
    policies = []
    for role in roles:
        role_perms = FIELD_PERMISSIONS.get(table, {}).get(role, {})
        policy = role_perms.get("delete")
        if policy:
            policies.append(policy)

    if "hard" in policies:
        return "hard"
    if "soft" in policies:
        return "soft"
    return None
