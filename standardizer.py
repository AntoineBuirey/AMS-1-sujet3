import string

def trim_punctuation(w: str) -> str:
    """Trim surrounding punctuation and lowercase the token."""
    return w.strip(string.punctuation).lower()

def normalize_apostrophes(w: str) -> str:
    """Normalize different apostrophe characters to standard apostrophe."""
    apostrophes = ["’", "‘", "`", "´"]
    for apos in apostrophes:
        w = w.replace(apos, "'")
    return w