

def validate_key(key: str) -> None:
    """Validate that the provided key is a valid hexadecimal string."""
    if not isinstance(key, str):
        raise ValueError("Key must be a string.")
    if not all(c in '0123456789abcdefABCDEF' for c in key):
        raise ValueError("Key must be a valid hexadecimal string.")