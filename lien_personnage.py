# links.py
import re
import json
import argparse
from collections import Counter, defaultdict
import os
import unicodedata
from typing import List, Dict, Tuple, Optional

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
    for name in characters:
        parts = re.findall(
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+'?[A-Za-zÀ-ÖØ-öø-ÿ0-9]+|"
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+\.|"
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+",
            name
        )
        parts = [lower_norm(p) for p in parts if p]
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
    occ_map = {name: find_occurrences_multi(tokens, name_to_parts[name]) for name in characters}
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

# ------------------ alias automatiques ------------------
def pretty_case(name: str) -> str:
    """Capitalize correctement, en corrigeant les initiales ('r.' -> 'R.')."""
    toks = name.split()
    out = []
    for t in toks:
        if len(t) == 2 and t[1] == "." and t[0].isalpha():
            out.append(t[0].upper() + ".")
        else:
            out.append(t[:1].upper() + t[1:].lower() if t else t)
    return " ".join(out)

def add_dominant_alias_by_ratio(
    alias: Dict[str, str],
    pair_counter: Counter,
    characters: Optional[List[str]] = None,
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
    alias: Dict[str, str] = {}

    # 1) normalisation casse
    for name in characters:
        alias[name] = pretty_case(name.lower())

    # Compte non orienté pour estimer co-liens
    pair_counter = Counter(raw_links) + Counter((b, a) for (a, b) in raw_links)

    # Index multi-mots / mono-token
    multiword = [n for n in characters if " " in n.strip()]
    single = [n for n in characters if " " not in n.strip()]

    def is_sub_token(short: str, long: str) -> bool:
        return short.lower() in long.lower().split()

    for s in single:
        cands = [mw for mw in multiword if is_sub_token(s, mw)]
        if not cands:
            continue
        scored = [(mw, pair_counter[(s, mw)]) for mw in cands]
        if not scored:
            continue
        scored.sort(key=lambda x: x[1], reverse=True)
        mw_best, c_best = scored[0]
        if c_best > 0 and (len(scored) == 1 or c_best >= 2 * scored[1][1]):
            alias[s] = alias.get(mw_best, mw_best)

    add_dominant_alias_by_ratio(alias, pair_counter, characters, ratio_thresh=0.50, min_count=3, gap=2)

    def find_canon(x: str) -> str:
        seen = set()
        while x in alias and alias[x] != x and alias[x] not in seen:
            seen.add(x)
            x = alias[x]
        return alias.get(x, x)

    for k in list(alias.keys()):
        alias[k] = find_canon(alias[k])

    return alias

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
# def load_wordcount(file_path: str) -> list[str]:
#     """Charger la liste des personnages depuis le fichier JSON."""
#     with open(file_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     return list(data.keys())


def build_links_file(
    input_file: str,
    characters:List[str],
    *,
    window: int = 25,
    aggregated: bool = False,
    min_count: int = 1,
    directed: bool = False,
    unique_per_window: bool = True,
) -> List[Tuple[str, str, int]]:
    """
    Génère le fichier de liens (brut ou agrégé) dans output/.
    Identique au main d'avant, mais réutilisable.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Fichier texte {input_file} introuvable.")

    prefix = os.path.splitext(os.path.basename(input_file))[0]
    # wordcount_file = f"output/{prefix}.wordcount.json"
    # if not os.path.exists(wordcount_file):
    #     raise FileNotFoundError(f"Fichier JSON {wordcount_file} introuvable.")

    # Charger texte + personnages
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()
    # characters = load_wordcount(wordcount_file)

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

    alias_map = infer_alias_map(characters, raw_links)
    pairs = canonicalize_links(raw_links, alias_map, undirected=not directed)

    result = []

    # Écriture dans output/
    os.makedirs("output", exist_ok=True)
    out = f"output/{prefix}_links.csv" if not aggregated else f"output/{prefix}_links_aggregated.csv"
    with open(out, "w", encoding="utf-8") as f:
        if aggregated:
            f.write("source,target,count\n")
            for (a, b), c in pairs.most_common():
                if c >= min_count:
                    f.write(f"{a},{b},{c}\n")
                    result.append((a, b, c))
        else:
            for (a, b), c in pairs.items():
                for _ in range(c):
                    f.write(f"{a},{b}\n")
                    result.append((a, b))

    print(f"✅ Liens sauvegardés dans {out}")
    return result
