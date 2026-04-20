import re
from collections import Counter, defaultdict
import os
import unicodedata
from typing import List, Dict, Tuple, Optional

from gamuLogger import Logger

Logger.set_module("linker")

PUNCT = ".,;:!?\"'()[]{}<>«»\u201c\u201d\u2018\u2019\u2014-\u2013\u2026"

def normalize_token(t: str) -> str:
    t = t.strip().strip(PUNCT)
    t = t.replace("\u2019", "'").replace("\u2026", "...")
    t = unicodedata.normalize("NFKC", t)
    return t

def lower_norm(t: str) -> str:
    return normalize_token(t).lower()

def tokenize_text(text: str) -> List[str]:
    return re.findall(
        r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+'?[A-Za-zÀ-ÖØ-öø-ÿ0-9]+|"
        r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+\.|"
        r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+|"
        r"\.{1,3}|[^\w\s]",
        text,
        flags=re.UNICODE
    )

def prepare_character_forms(characters: List[str]) -> Dict[str, List[str]]:
    name_to_parts: Dict[str, List[str]] = {}
    PARTICLES = {"de", "du", "des", "von", "van", "le", "la"}
    for name in characters:
        parts = re.findall(
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+'?[A-Za-zÀ-ÖØ-öø-ÿ0-9]+|"
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+\.|"
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+",
            name
        )
        parts = [lower_norm(p) for p in parts if p and (len(p) > 1 or p.lower() in PARTICLES)]
        if parts:
            name_to_parts[name] = parts
    return name_to_parts

def find_occurrences_multi(tokens: List[str], parts: List[str]) -> List[int]:
    if not parts:
        return []
    L, n = len(tokens), len(parts)
    low = [lower_norm(t) for t in tokens]
    hits: List[int] = []
    i = 0
    while i <= L - n:
        if all(low[i + k] == parts[k] for k in range(n)):
            hits.append(i)
            i += n
        else:
            i += 1
    return hits

def build_raw_links_with_positions(
    characters: List[str],
    tokens: List[str],
    name_to_parts: Dict[str, List[str]],
    window: int = 25,
    undirected: bool = True,
    unique_per_window: bool = True,
) -> List[Tuple[str, str, int, int]]:
    """Retourne (a, b, pos_a, pos_b) pour chaque co-occurrence."""
    occ_map = {
        name: find_occurrences_multi(tokens, name_to_parts[name])
        for name in characters if name in name_to_parts
    }
    links: List[Tuple[str, str, int, int]] = []
    for a in characters:
        occ_a = occ_map.get(a, [])
        if not occ_a:
            continue
        for idx_a in occ_a:
            start = max(0, idx_a - window)
            end   = min(len(tokens), idx_a + window + 1)
            seen  = set()
            for b in characters:
                if b == a:
                    continue
                for idx_b in occ_map.get(b, []):
                    if start <= idx_b < end:
                        key = (a, b) if not undirected else tuple(sorted((a, b)))
                        if unique_per_window:
                            if key in seen:
                                break
                            seen.add(key)
                        links.append((a, b, idx_a, idx_b))
                        break
    return links

def build_raw_links(
    characters, tokens, name_to_parts, window=25, undirected=True, unique_per_window=True
) -> List[Tuple[str, str]]:
    return [(a, b) for a, b, _, _ in build_raw_links_with_positions(
        characters, tokens, name_to_parts, window, undirected, unique_per_window
    )]

def add_dominant_alias_by_ratio(alias, pair_counter, *, ratio_thresh=0.50, min_count=3, gap=2):
    totals: Dict[str, int] = defaultdict(int)
    for (a, b), c in pair_counter.items():
        totals[a] += c
        totals[b] += c
    for name, total in totals.items():
        if total < min_count:
            continue
        partners = [(b, c) for (a, b), c in pair_counter.items() if a == name]
        partners += [(a, c) for (a, b), c in pair_counter.items() if b == name]
        if not partners:
            continue
        partners.sort(key=lambda x: x[1], reverse=True)
        top_name, c_top = partners[0]
        c_second = partners[1][1] if len(partners) > 1 else 0
        if " " in top_name.strip() and ((c_top / max(total, 1)) >= ratio_thresh or c_top >= c_second + gap):
            alias[name] = alias.get(top_name, top_name)

def infer_alias_map(characters, raw_links):
    alias = {name: name for name in characters}
    unique_names   = list(set(alias.values()))
    simple_names   = [n for n in unique_names if len(n.split()) == 1]
    compound_names = [n for n in unique_names if len(n.split()) > 1]
    for simple in simple_names:
        matches = [c for c in compound_names if simple in c.split()]
        if len(matches) == 1:
            for key, val in alias.items():
                if val == simple:
                    alias[key] = matches[0]
    mapped_links = [(alias.get(a, a), alias.get(b, b)) for a, b in raw_links]
    pair_counter = Counter(mapped_links) + Counter((b, a) for (a, b) in mapped_links)
    add_dominant_alias_by_ratio(alias, pair_counter)
    def find_canon(x):
        seen = set()
        while x in alias and alias[x] != x and alias[x] not in seen:
            seen.add(x); x = alias[x]
        return alias.get(x, x)
    for k in list(alias.keys()):
        alias[k] = find_canon(alias[k])
    return alias

def canonicalize_links(raw_links, alias_map, undirected=True):
    agg = Counter()
    for a, b in raw_links:
        A, B = alias_map.get(a, a), alias_map.get(b, b)
        if A == B:
            continue
        if undirected and A > B:
            A, B = B, A
        agg[(A, B)] += 1
    return agg

def build_links_file(
    input_file: str,
    characters: List[str],
    *,
    window: int = 25,
    aggregated: bool = False,
    min_count: int = 1,
    directed: bool = False,
    unique_per_window: bool = True,
    external_alias_map: Optional[Dict[str, str]] = None,
    compute_polarity: bool = False,
) -> List[Tuple]:
    """
    Génère les liens entre personnages.

    compute_polarity=True : ajoute une polarité à chaque lien.
      aggregated=True  → (a, b, weight, polarity)
      aggregated=False → (a, b, polarity)
    polarity : +1 positif, -1 négatif, 0 neutre.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Fichier texte {input_file} introuvable.")

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    tokens        = tokenize_text(text)
    name_to_parts = prepare_character_forms(characters)

    raw_links_full = build_raw_links_with_positions(
        characters, tokens, name_to_parts,
        window=window, undirected=not directed, unique_per_window=unique_per_window,
    )
    raw_links = [(a, b) for a, b, _, _ in raw_links_full]

    alias_map = external_alias_map if external_alias_map is not None else infer_alias_map(characters, raw_links)
    pairs     = canonicalize_links(raw_links, alias_map, undirected=not directed)

    # Calcul de la polarité
    polarity_map: Dict[Tuple[str, str], int] = {}
    if compute_polarity:
        Logger.info("Calcul de la polarité des relations…")
        try:
            from .relation_polarity import compute_signed_links
            canon_chars = list({alias_map.get(c, c) for c in characters})
            canon_n2p   = prepare_character_forms(canon_chars)
            raw_canon   = [(alias_map.get(a, a), alias_map.get(b, b))
                           for a, b in raw_links
                           if alias_map.get(a, a) != alias_map.get(b, b)]
            polarity_map = compute_signed_links(canon_chars, tokens, canon_n2p, raw_canon, window)
        except Exception as e:
            Logger.warning(f"Polarité ignorée : {e}")

    result = []
    if aggregated:
        for (a, b), c in pairs.most_common():
            if c >= min_count:
                key = tuple(sorted((a, b)))
                if compute_polarity:
                    result.append((a, b, c, polarity_map.get(key, 0)))
                else:
                    result.append((a, b, c))
    else:
        for (a, b), c in pairs.items():
            key = tuple(sorted((a, b)))
            for _ in range(c):
                if compute_polarity:
                    result.append((a, b, polarity_map.get(key, 0)))
                else:
                    result.append((a, b))
    return result