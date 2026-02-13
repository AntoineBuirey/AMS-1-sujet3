# networker/spacy_helper.py
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Sequence, Tuple
import re
import unicodedata

import spacy
from spacy.language import Language


# --- Domain helpers ---------------------------------------------------------

# Small set of highly-recurring Foundation entities that spaCy FR may miss.
# We use an EntityRuler to boost recall on PER/LOC/ORG for this corpus.
# You can extend these lists safely.
FOUNDATION_PER: Sequence[str] = (
    "hari seldon",
    "seldon",
    "dors",
    "daneel",
    "r. daneel",
    "r daneel",
    "elijah baley",
    "baley",
    "cleon",
    "demerzel",
    "hummin",
    "raych",
    "amaryl",
)

FOUNDATION_LOC: Sequence[str] = (
    "trantor",
    "helicon",
)

FOUNDATION_ORG: Sequence[str] = (
    "encyclopaedia galactica",
)


def _strip_accents(s: str) -> str:
    # NFKD splits accents; we then drop combining marks.
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def _normalize_text(s: str) -> str:
    s = s.replace("_", " ")
    s = s.replace("’", "'")
    s = _strip_accents(s)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _clean_for_spacy(text: str) -> str:
    # spaCy likes regular spaces; normalize whitespace.
    text = text.replace("_", " ")
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _add_foundation_ruler(nlp: Language) -> None:
    """Add a lightweight EntityRuler before NER.

    This increases recall on common entities in the books.
    """
    if "entity_ruler" in nlp.pipe_names:
        return

    ruler = nlp.add_pipe("entity_ruler", before="ner")
    patterns = []

    # Longest phrases first helps matching multiword entities.
    for name in sorted(set(FOUNDATION_PER), key=len, reverse=True):
        patterns.append({"label": "PER", "pattern": name})
    for name in sorted(set(FOUNDATION_LOC), key=len, reverse=True):
        patterns.append({"label": "LOC", "pattern": name})
    for name in sorted(set(FOUNDATION_ORG), key=len, reverse=True):
        patterns.append({"label": "ORG", "pattern": name})

    ruler.add_patterns(patterns)


@lru_cache(maxsize=1)
def get_nlp() -> Language:
    """Load spaCy French model with fallback.

    Tries: fr_core_news_md -> fr_core_news_sm.
    Adds an EntityRuler for domain entities.
    """
    # Try the better model first if installed.
    for model in ("fr_core_news_md", "fr_core_news_sm"):
        try:
            nlp = spacy.load(model)
            break
        except OSError:
            nlp = None
    if nlp is None:
        # Clear error for user if no model installed.
        raise OSError(
            "spaCy French model not found. Install one of: 'fr_core_news_sm' or 'fr_core_news_md'."
        )

    # Ensure we have sentence boundaries even if parser is disabled in some installs.
    if "sentencizer" not in nlp.pipe_names:
        try:
            nlp.add_pipe("sentencizer")
        except Exception:
            pass

    # Add domain ruler to improve recall.
    _add_foundation_ruler(nlp)
    return nlp


@lru_cache(maxsize=50_000)
def _cached_labels(sentence_text_norm: str) -> Dict[str, str]:
    """Cache entity extraction per normalized sentence text."""
    nlp = get_nlp()
    doc = nlp(_clean_for_spacy(sentence_text_norm))

    # Keep longest spans first to reduce collisions (e.g., "hari" vs "hari seldon").
    ents = sorted(doc.ents, key=lambda e: len(e.text), reverse=True)

    out: Dict[str, str] = {}
    for ent in ents:
        mention = _normalize_text(ent.text)
        if not mention:
            continue
        # Prefer first (longest) occurrence.
        if mention not in out:
            out[mention] = ent.label_
    return out


def extract_person_mentions(sentence_tokens: List[str]) -> Dict[str, str]:
    """Return {normalized_mention: spacy_label} for a sentence.

    Example: {"hari seldon": "PER", "trantor": "LOC"}

    NOTE: despite the name, this returns all entity labels; caller can filter.
    """
    text_norm = _normalize_text(" ".join(sentence_tokens))
    return dict(_cached_labels(text_norm))


def spacy_label_for_token(
    sentence_tokens: List[str],
    index: int,
    allowed_labels: Tuple[str, ...] = ("PER", "LOC", "ORG", "MISC"),
) -> str:
    """Try to match a spaCy entity around a token.

    Tests 1- to 4-grams around `index` (token, bigram, trigram, quadgram).
    Returns one of allowed labels or "".
    """
    labels = extract_person_mentions(sentence_tokens)

    def add_candidate(parts: List[str], start: int, end: int, out: List[str]) -> None:
        if 0 <= start < len(parts) and 0 < end <= len(parts) and start < end:
            out.append(" ".join(parts[start:end]))

    parts = [t.replace("_", " ") for t in sentence_tokens]
    candidates: List[str] = []

    # 1-gram
    add_candidate(parts, index, index + 1, candidates)

    # 2-gram (right/left)
    add_candidate(parts, index, index + 2, candidates)
    add_candidate(parts, index - 1, index + 1, candidates)

    # 3-gram
    add_candidate(parts, index, index + 3, candidates)
    add_candidate(parts, index - 2, index + 1, candidates)

    # 4-gram (helps with variants like "r. daneel olivaw")
    add_candidate(parts, index, index + 4, candidates)
    add_candidate(parts, index - 3, index + 1, candidates)

    # Prefer longer matches first.
    candidates = sorted(set(candidates), key=len, reverse=True)

    for c in candidates:
        c_norm = _normalize_text(c)
        lab = labels.get(c_norm, "")
        if lab and lab in allowed_labels:
            return lab
    return ""