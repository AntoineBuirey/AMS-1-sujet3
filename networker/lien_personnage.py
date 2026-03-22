import re
from collections import Counter, defaultdict
import os
import unicodedata
from typing import List, Dict, Tuple

from gamuLogger import Logger

Logger.set_module("linker")

# ------------------ tokenisation/normalisation ------------------
PUNCT = ".,;:!?\"'()[]{}<>«»“”‘’—-–…"

def normalize_token(t: str) -> str:
    t = t.strip().strip(PUNCT)
    t = t.replace("’", "'").replace("…", "...")
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

# ------------------ multi-mots pour personnages ------------------
def prepare_character_forms(characters: List[str]) -> Dict[str, List[str]]: 
    name_to_parts: Dict[str, List[str]] = {}
    PARTICLES = {"de", "du", "des", "von", "van", "le", "la"}  # particules nobles
    
    for name in characters:
        parts = re.findall(
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+'?[A-Za-zÀ-ÖØ-öø-ÿ0-9]+|"
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+\.|"
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+",
            name
        )
        # Conserver les particules dans les noms
        parts = [lower_norm(p) for p in parts if p and (len(p) > 1 or p. lower() in PARTICLES)]
        if parts:
            name_to_parts[name] = parts
    return name_to_parts

def find_occurrences_multi(tokens: List[str], parts: List[str]) -> List[int]:
    if not parts:
        return []
    L = len(tokens)
    n = len(parts)
    low = [lower_norm(t) for t in tokens]
    hits: List[int] = []
    i = 0
    while i <= L - n:
        if all(low[i + k] == parts[k] for k in range(n)):
            hits.append(i)
            i += n  # évite chevauchement direct
        else:
            i += 1
    return hits

# ------------------ liens bruts ------------------
def build_raw_links(characters: List[str],
                    tokens: List[str],
                    name_to_parts: Dict[str, List[str]],
                    window: int = 25,
                    undirected: bool = True,
                    unique_per_window: bool = True) -> List[Tuple[str, str]]:
    Logger.debug(f"{name_to_parts}\n{characters}")
    occ_map = {name: find_occurrences_multi(tokens, name_to_parts[name]) for name in characters if name in name_to_parts}
    links: List[Tuple[str, str]] = []
    for a in characters:
        occ_a = occ_map.get(a, [])
        if not occ_a:
            continue
        for idx in occ_a:
            start = max(0, idx - window)
            end = min(len(tokens), idx + window + 1)
            seen = set()
            for b in characters:
                if b == a:
                    continue
                for j in occ_map.get(b, []):
                    if start <= j < end:
                        key = (a, b) if not undirected else tuple(sorted((a, b)))
                        if unique_per_window:
                            if key in seen:
                                break
                            seen.add(key)
                        links.append((a, b))
                        break
    return links

def add_dominant_alias_by_ratio(
    alias: Dict[str, str],
    pair_counter: Counter,
    *,
    ratio_thresh: float = 0.50,   
    min_count: int = 3,
    gap: int = 2                 
) -> None:
    """
    Mappe automatiquement un nom vers son partenaire majoritaire.
    Exemple: 'Le Commissaire' -> 'Julius Enderby' si ce dernier est le top
    partenaire (multi-mots) avec dominance par ratio ou par écart.
    """
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

        dominant_by_ratio = (c_top / max(total, 1)) >= ratio_thresh
        dominant_by_gap = (c_top >= c_second + gap)
        is_multiword_target = (" " in top_name.strip())

        if is_multiword_target and (dominant_by_ratio or dominant_by_gap):
            alias[name] = alias.get(top_name, top_name)

def infer_alias_map(characters: List[str], raw_links: List[Tuple[str, str]]) -> Dict[str, str]:
    alias:  Dict[str, str] = {}
    
    # 1) Normalisation avec Pretty Case
    for name in characters:
        # alias[name] = pretty_case(name.lower())
        alias[name] = name
    
    # 2) Détection des prénoms/noms seuls
    unique_names = list(set(alias.values()))
    
    # Séparer les noms simples (1 mot) des noms composés
    simple_names = [n for n in unique_names if len(n. split()) == 1]
    compound_names = [n for n in unique_names if len(n. split()) > 1]
    
    # Ne fusionner que si le nom simple apparaît DANS le nom composé
    # ET s'il n'y a qu'un seul match possible
    for simple in simple_names:
        matches = [c for c in compound_names if simple in c. split()]
        if len(matches) == 1:  # Fusion uniquement si pas d'ambiguïté
            # Remplacer toutes les occurrences
            for key, val in alias.items():
                if val == simple:
                    alias[key] = matches[0]
    # -------------------------------------------------------------------

    # 2) Statistiques de co-occurrence (pour les surnoms comme "Le Commissaire")
    
    # On recalcule les paires basées sur les nouveaux alias fusionnés
    mapped_links = []
    for a, b in raw_links:
        mapped_links.append((alias.get(a, a), alias.get(b, b)))

    pair_counter = Counter(mapped_links) + Counter((b, a) for (a, b) in mapped_links)
    
    # On tente de lier les noms restants qui n'ont pas été fusionnés par inclusion
    # (Par exemple "Le Commissaire" -> "Julius Enderby")
    add_dominant_alias_by_ratio(alias, pair_counter, ratio_thresh=0.50, min_count=3, gap=2)

    # 3) Nettoyage final des chaînes d'alias (A->B->C  ==> A->C)
    def find_canon(x: str) -> str:
        seen = set()
        while x in alias and alias[x] != x and alias[x] not in seen:
            seen.add(x)
            x = alias[x]
        return alias.get(x, x)

    for k in list(alias.keys()):
        alias[k] = find_canon(alias[k])

    return alias

# ------------------ canonicalisation des liens ------------------
def canonicalize_links(raw_links: List[Tuple[str, str]],
                       alias_map: Dict[str, str],
                       undirected: bool = True) -> Counter:
    agg = Counter()
    for a, b in raw_links:
        A = alias_map.get(a, a)
        B = alias_map.get(b, b)
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
    external_alias_map: Dict[str, str] | None = None,
) -> List[Tuple[str, str, int]]:
    """
    Génère le fichier de liens (brut ou agrégé) dans output/.

    Si external_alias_map est fourni (dict nom_brut -> nom_canonique), il est utilisé
    directement et infer_alias_map est ignoré, évitant ainsi une double résolution
    d'alias incohérente avec resolve_aliases().
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Fichier texte {input_file} introuvable.")

    # Charger texte + personnages
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    # Tokens + formes multi-mots
    tokens = tokenize_text(text)
    name_to_parts = prepare_character_forms(characters)

    # Liens bruts
    raw_links = build_raw_links(
        characters, tokens, name_to_parts,
        window=window,
        undirected=not directed,
        unique_per_window=unique_per_window
    )

    # Résolution d'alias : on utilise la map externe si fournie,
    # sinon on recalcule en interne (comportement historique).
    if external_alias_map is not None:
        alias_map = external_alias_map
        Logger.debug("Using external alias map (infer_alias_map skipped).")
    else:
        alias_map = infer_alias_map(characters, raw_links)

    pairs = canonicalize_links(raw_links, alias_map, undirected=not directed)

    result = []

    if aggregated:
        for (a, b), c in pairs.most_common():
            if c >= min_count:
                result.append((a, b, c))
    else:
        for (a, b), c in pairs.items():
            for _ in range(c):
                result.append((a, b))

    return result