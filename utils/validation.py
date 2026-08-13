import re


PIN_PATTERN = re.compile(r"^[0-9]{4,12}$")


def normalize_pin(pin: str) -> str:
    candidate = pin.strip()
    if not PIN_PATTERN.fullmatch(candidate):
        raise ValueError("PIN must contain 4 to 12 digits")
    return candidate
