from fastapi import Request


def wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "application/json" in accept or request.query_params.get("format") == "json"
