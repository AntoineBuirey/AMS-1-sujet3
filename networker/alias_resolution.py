from gamuLogger import Logger
import json
import os
import re

from .data_objects import DataObject as DO

ALIAS_MAP_PATH = "networker/data/alias_map.json"

PARTICLES = {"de", "du", "des", "von", "van", "le", "la", "les", "l", "d"}
TITLES    = {"mr", "mme", "dr", "m", "sir", "dame", "capitaine",
             "lieutenant", "sergent", "professeur", "prof", "maitre"}


def part_score(part1: str, part2: str) -> float:
    if part1 == part2:
        return 1.0
    len1, len2 = len(part1), len(part2)
    if len1 == 0 or len2 == 0:
        return 0.0
    if min(len1, len2) / max(len1, len2) < 0.5:
        return 0.0
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if part1[i - 1] == part2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return (max(len1, len2) - dp[len1][len2]) / max(len1, len2)


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower().replace("_", " ")
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def strip_article(norm: str) -> str:
    """
    Supprime l'article défini en tête pour permettre la fusion de variantes.
    Cas compacte (apostrophe supprimée par normalize_name) :
      normalize_name("l'Empereur") → "lempereur"  → strip → "empereur"
      normalize_name("L'Empereur") → "lempereur"  → strip → "empereur"
      normalize_name("Empereur")   → "empereur"   → strip → "empereur"
    Cas avec espace :
      "le commissaire" → "commissaire"
      "la reine"       → "reine"
    """
    # Cas compacte : "l" ou "d" collé (apostrophe supprimée)
    for prefix in ("l", "d"):
        if norm.startswith(prefix) and len(norm) > len(prefix) + 1:
            candidate = norm[len(prefix):]
            if len(candidate) >= 3:
                norm = candidate
                break
    # Cas avec espace
    for article in ("le ", "la ", "les ", "un ", "une ", "des ", "du "):
        if norm.startswith(article):
            norm = norm[len(article):]
            break
    return norm.strip()


def _meaningful_tokens(norm: str) -> list[str]:
    return [t for t in norm.split() if t not in PARTICLES and t not in TITLES and len(t) > 1]


def load_alias_map() -> list[list[str]]:
    if not os.path.exists(ALIAS_MAP_PATH):
        Logger.warning(f"Fichier d'alias non trouvé : {ALIAS_MAP_PATH}")
        return []
    try:
        with open(ALIAS_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [
                [normalize_name(name) for name in group]
                for group in data
                if isinstance(group, list) and group
            ]
        return []
    except Exception as e:
        Logger.error(f"Erreur lors du chargement de l'alias map : {e}")
        return []


def resolve_aliases(persons: list[str],
                    word_count: dict[str, DO.WordOccurence] | None = None) -> list[list[str]]:
    """
    Regroupe les alias d'une liste de noms de personnages.

    v3 — article stripping :
    Fusionne les variantes avec/sans article : "l'Empereur", "L'Empereur", "Empereur"
    deviennent un seul groupe car strip_article donne "empereur" dans les trois cas.
    """
    manual_groups = load_alias_map()
    normalized_persons = [normalize_name(p) for p in persons]
    stripped_persons   = [strip_article(n) for n in normalized_persons]
    alias_pairs: list[tuple[str, str]] = []

    for i, name1 in enumerate(persons):
        norm1     = normalized_persons[i]
        stripped1 = stripped_persons[i]
        mtok1     = _meaningful_tokens(norm1)

        for j in range(i + 1, len(persons)):
            name2     = persons[j]
            norm2     = normalized_persons[j]
            stripped2 = stripped_persons[j]
            mtok2     = _meaningful_tokens(norm2)

            # A — Alias manuel
            is_manual = False
            for group in manual_groups:
                if norm1 in group and norm2 in group:
                    alias_pairs.append((name1, name2))
                    is_manual = True
                    break
            if is_manual:
                continue

            # B — Sécurité mono-mot SAUF si stripped identique
            # (ex : "Empereur" vs "l'Empereur" → stripped == "empereur" → OK)
            if len(norm1.split()) == 1 and len(norm2.split()) == 1:
                if stripped1 == stripped2 and len(stripped1) >= 3:
                    alias_pairs.append((name1, name2))
                continue

            # C — Fusion par article stripping
            # "l'Empereur" (stripped="emperor") == "Empereur" (stripped="emperor")
            if stripped1 == stripped2 and len(stripped1) >= 3:
                alias_pairs.append((name1, name2))
                continue

            # D — Inclusion sûre
            if mtok1 and mtok2:
                if any(t in mtok2 for t in mtok1) or any(t in mtok1 for t in mtok2):
                    alias_pairs.append((name1, name2))
                    continue

            # E — Levenshtein (0.92)
            if part_score(norm1, norm2) >= 0.92:
                alias_pairs.append((name1, name2))

    final_groups: list[set[str]] = []

    for m_group in manual_groups:
        existing = {p for p, n in zip(persons, normalized_persons) if n in m_group}
        if existing:
            final_groups.append(existing)

    for a1, a2 in alias_pairs:
        found_group = None
        for group in list(final_groups):
            if a1 in group or a2 in group:
                if found_group is None:
                    group.update([a1, a2])
                    found_group = group
                else:
                    found_group.update(group)
                    final_groups.remove(group)
                    break
        if found_group is None:
            final_groups.append({a1, a2})

    for person in persons:
        if not any(person in g for g in final_groups):
            final_groups.append({person})

    def sort_key(name: str) -> int:
        if word_count:
            return word_count.get(name, DO.WordOccurence(0, [])).quantity
        return len(name.split())

    return [sorted(g, key=sort_key, reverse=True) for g in final_groups]