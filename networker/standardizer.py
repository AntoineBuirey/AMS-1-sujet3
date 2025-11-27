import string
from typing import Any, TypeVar

def trim_punctuation(w: str) -> str:
    """Trim surrounding punctuation and lowercase the token."""
    return w.strip(string.punctuation).lower()

def normalize_apostrophes(w: str) -> str:
    """Normalize different apostrophe characters to standard apostrophe."""
    apostrophes = ["’", "‘", "`", "´"]
    for apos in apostrophes:
        w = w.replace(apos, "'")
    return w


T = TypeVar('T', str, list[Any], dict[Any, Any], tuple[Any, ...], set[Any])
def lowercase(item: T) -> T:
    """Lowercase strings or iterables of strings."""
    if isinstance(item, str):
        return item.lower()
    elif isinstance(item, list):
        return [lowercase(elem) for elem in item]
    elif isinstance(item, dict):
        return {lowercase(key): lowercase(value) for key, value in item.items()}
    elif isinstance(item, tuple):
        return tuple(lowercase(elem) for elem in item)
    elif isinstance(item, set):
        return {lowercase(elem) for elem in item}
    else:
        return item
    
def capitalize_all_words(s: str) -> str:
    """Uppercase all words in a string."""
    return ' '.join(word.capitalize() for word in s.split())