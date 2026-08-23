"""Minimal authentication behavior for the public InstrProof demo."""


def authenticate(token: str) -> bool:
    """Return whether a non-empty token was supplied."""
    return bool(token.strip())
