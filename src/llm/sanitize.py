"""Defend against prompt injection using simple, clean data delimiters."""

def wrap_untrusted(text: str) -> str:
    """
    Wrap untrusted content cleanly.
    Keeps the instruction footprint low to avoid distracting 1B models.
    """
    # Simple, high-contrast structural separator
    return (
        "[START UNTRUSTED DATA]\n"
        f"{text.strip()}\n"
        "[END UNTRUSTED DATA]"
    )