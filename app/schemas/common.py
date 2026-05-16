def normalize_required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(f"{field_name} must not be empty")

    if len(normalized_value) > 200:
        raise ValueError(f"{field_name} length must be between 1 and 200")

    return normalized_value