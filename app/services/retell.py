def extract_city(payload: dict) -> str | None:
    args = payload.get("args")
    if isinstance(args, dict) and args.get("city"):
        return str(args["city"]).strip()

    if payload.get("city"):
        return str(payload["city"]).strip()

    body = payload.get("body")
    if isinstance(body, dict):
        return extract_city(body)

    return None


def extract_caller_phone(payload: dict) -> str | None:
    call = payload.get("call")
    if not isinstance(call, dict):
        body = payload.get("body")
        if isinstance(body, dict):
            return extract_caller_phone(body)
        return None

    phone = call.get("from_number") or call.get("user_number")
    if call.get("direction") == "outbound":
        phone = call.get("to_number") or call.get("user_number") or phone

    if not phone:
        return None

    phone = str(phone).strip()
    if not phone.startswith("+"):
        digits = "".join(ch for ch in phone if ch.isdigit())
        if digits:
            phone = f"+{digits}"

    return phone or None
