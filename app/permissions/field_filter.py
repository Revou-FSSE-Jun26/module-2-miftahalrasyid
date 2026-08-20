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


def filter_fields(data: dict, table: str, roles: list, operation: str) -> dict:
    """
    Filter a dict to only include fields the user's roles are allowed to write/read.
    Used for update operations where data is a plain dict.
    """
    allowed = get_allowed_fields(table, roles, operation)
    return {k: v for k, v in data.items() if k in allowed}


def filter_model_fields(instance, table: str, roles: list, operation: str, defaults: dict = None):
    """
    Reset fields on a model instance that the user's roles are NOT allowed to write.
    Used for create operations where load_instance=True produces a model object.
    
    Args:
        instance: SQLAlchemy model instance
        table: table name key in FIELD_PERMISSIONS
        roles: list of role strings from JWT
        operation: "create" or "update"
        defaults: dict of field_name -> default_value to reset unauthorized fields to
    """
    if defaults is None:
        defaults = {}
    
    allowed = get_allowed_fields(table, roles, operation)
    all_controlled_fields = set()
    
    # Gather all fields that ANY role can control for this table+operation
    for role_perms in FIELD_PERMISSIONS.get(table, {}).values():
        fields = role_perms.get(operation, set())
        if isinstance(fields, set):
            all_controlled_fields |= fields
    
    # Reset fields that are controlled but NOT allowed for this user
    for field in all_controlled_fields - allowed:
        if hasattr(instance, field):
            default_val = defaults.get(field)
            setattr(instance, field, default_val)
    
    return instance
