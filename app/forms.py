from pydantic import ValidationError


def format_validation_error(error: ValidationError) -> str:
    parts = []
    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"])
        parts.append(f"{field}: {item['msg']}")
    return "; ".join(parts)
