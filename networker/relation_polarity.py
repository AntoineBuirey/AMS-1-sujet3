"""
relation_polarity.py  v4 — hybride JSON + auto-enrichissement
==============================================================
Détecte la polarité des relations entre personnages.

Architecture :
  1. Fichier JSON de base (networker/data/relation_pairs.json)
     Contient les paires dont la polarité est connue a priori ou déjà apprise.
     Peut être vide au premier run — il se remplira automatiquement.
     Format : [{"a": "baley", "b": "daneel", "polarity": 1}, ...]

  2. Registre en mémoire (accumulation par livre)
     Accumule les scores bruts de co-occurrence chapitre après chapitre.
     Permet au signal de s'accumuler sur tout le livre.

  3. Auto-enrichissement
     Quand un signal lexical est suffisamment fort (|mean| > AUTO_SAVE_THRESHOLD),
     la paire et sa polarité sont automatiquement sauvegardées dans le JSON.
     Les runs suivants bénéficient immédiatement de ce prior appris.

Valeurs : +1 positif, -1 négatif, 0 neutre.
"""

from __future__ import annotations
import unicodedata
import json
import os
from collections import defaultdict
from typing import List, Tuple, Dict
from gamuLogger import Logger

Logger.set_module("polarity")

# =============================================================================
# CHEMINS
# =============================================================================
_DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_PAIRS_FILE = os.path.join(_DATA_DIR, "relation_pairs.json")

# =============================================================================
# SEUILS
# =============================================================================
THRESHOLD_MEAN     = 0.4    # signal moyen minimal pour décider
THRESHOLD_RATIO    = 0.45   # ratio dominant minimal
AUTO_SAVE_THRESHOLD = 1.2   # signal minimal pour auto-enrichir le JSON

# =============================================================================
# ÉTAT GLOBAL
# =============================================================================
# Paires connues : chargées depuis le JSON + apprises en cours de run
_known_pairs: Dict[Tuple[str, str], int] = {}

# Registre des scores bruts accumulés sur le livre en cours
_book_scores: Dict[Tuple[str, str], List[float]] = defaultdict(list)

# Paires nouvellement apprises (à sauvegarder en fin de run)
_newly_learned: Dict[Tuple[str, str], int] = {}


# =============================================================================
# UTILITAIRES
# =============================================================================

def _normalize(s: str) -> str:
    """
    Normalise un nom exactement comme normalize_name() dans alias_resolution.py :
    - minuscules
    - remplace les apostrophes typographiques par droites AVANT NFKD
    - insère un espace après un point collé (R.Daneel → r daneel)
    - supprime toute la ponctuation (apostrophes, tirets, points...)
    - réduit les espaces multiples
    Garantit que les clés polarity correspondent aux clés alias.
    """
    import re as _re
    s = s.lower().strip()
    # Normaliser tous les types d'apostrophes et guillemets
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u2032", "'")
    # Point collé : r.daneel → r. daneel (avant suppression ponctuation)
    s = _re.sub(r"\.([a-zA-Z\u00C0-\u00FF])", r" \1", s)
    # NFKD pour les accents
    s = unicodedata.normalize("NFKD", s)
    # Supprimer tout ce qui n'est pas lettre, chiffre ou espace
    s = "".join(c for c in s if c.isalnum() or c.isspace())
    s = _re.sub(r"\s+", " ", s).strip()
    return s


def _make_key(a: str, b: str) -> Tuple[str, str]:
    na, nb = _normalize(a), _normalize(b)
    return (na, nb) if na <= nb else (nb, na)


def _lemmatize_simple(t: str) -> List[str]:
    candidates = [t]
    for suffix, repl in [
        ("aient", "er"), ("eront", "er"), ("issait", "ir"),
        ("issent", "ir"), ("erais", "er"), ("erait", "er"),
        ("ait", "er"), ("ait", "ir"), ("ont", "er"),
        ("ons", "er"), ("ez", "er"), ("es", "er"), ("e", "er"),
        ("it", "re"), ("ut", "re"),
    ]:
        if t.endswith(suffix) and len(t) > len(suffix) + 3:
            candidates.append(t[: -len(suffix)] + repl)
    return candidates


def _is_negated(tl: List[str], idx: int, radius: int = 4) -> bool:
    start = max(0, idx - radius)
    end   = min(len(tl), idx + radius + 1)
    return any(w in _NEGATION_WORDS for w in tl[start:end])


# =============================================================================
# CHARGEMENT / SAUVEGARDE DU JSON
# =============================================================================

def load_pairs() -> None:
    """Charge les paires connues depuis le JSON."""
    global _known_pairs
    _known_pairs = {}
    if not os.path.exists(_PAIRS_FILE):
        Logger.info("relation_pairs.json absent — démarrage sans prior.")
        return
    try:
        with open(_PAIRS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            key = _make_key(entry["a"], entry["b"])
            _known_pairs[key] = int(entry["polarity"])
        Logger.info(f"relation_pairs.json : {len(_known_pairs)} paires chargées")
    except Exception as e:
        Logger.error(f"Erreur chargement relation_pairs.json : {e}")


def save_pairs() -> None:
    """
    Sauvegarde toutes les paires connues dans le JSON (base + apprises).
    Déduplique en utilisant des clés frozenset pour éviter les doublons
    dus à l'ordre des noms (a/b vs b/a).
    """
    if not _newly_learned:
        return

    # Fusionner en dédupliquant par frozenset
    merged: Dict[Tuple[str, str], int] = {}
    for (a, b), pol in list(_known_pairs.items()) + list(_newly_learned.items()):
        ka, kb = (a, b) if a <= b else (b, a)
        merged[(ka, kb)] = pol  # last-write-wins, mais les valeurs sont cohérentes

    os.makedirs(_DATA_DIR, exist_ok=True)
    output = [
        {"a": a, "b": b, "polarity": pol}
        for (a, b), pol in sorted(merged.items())
    ]
    with open(_PAIRS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    Logger.info(
        f"relation_pairs.json enrichi : +{len(_newly_learned)} nouvelles paires "
        f"({len(merged)} total)"
    )
    _known_pairs.update(_newly_learned)
    _newly_learned.clear()


def reset_book_scores() -> None:
    """Vide le registre entre deux livres."""
    _book_scores.clear()


# =============================================================================
# LEXIQUES
# =============================================================================

_POSITIVE_VERBS: frozenset[str] = frozenset({
    "aimer", "adorer", "chérir", "apprécier", "vénérer", "affectionner",
    "confier", "allier", "soutenir", "appuyer", "défendre", "protéger",
    "aider", "assister", "secourir", "sauver", "rejoindre", "unir",
    "rallier", "coopérer", "collaborer", "partager", "réconcilier",
    "sourire", "rire", "remercier", "féliciter", "complimenter",
    "encourager", "rassurer", "consoler", "réconforter",
    "respecter", "admirer", "honorer", "saluer", "reconnaître",
    "approuver", "accepter", "accueillir", "escorter", "accompagner",
    "guider", "enseigner",
    "ami", "amie", "compagnon", "compagne", "camarade",
    "allié", "alliée", "partenaire", "équipier",
    "fidèle", "loyal", "loyale", "dévoué", "dévouée",
    "confiance", "amitié", "solidarité", "alliance", "accord",
    "tendresse", "affection", "amour",
})

_NEGATIVE_VERBS: frozenset[str] = frozenset({
    "tuer", "assassiner", "frapper", "battre", "blesser", "attaquer",
    "poignarder", "étrangler", "abattre", "éliminer", "exécuter",
    "torturer", "emprisonner", "arrêter", "capturer", "chasser",
    "expulser", "bannir", "condamner",
    "haïr", "détester", "maudire", "insulter", "accuser", "dénoncer",
    "trahir", "abandonner", "rejeter", "mépriser", "humilier",
    "ridiculiser", "moquer", "railler",
    "mentir", "tromper", "manipuler", "piéger", "comploter",
    "conspirer", "espionner", "surveiller", "contraindre",
    "combattre", "affronter", "défier", "résister",
    "contester", "menacer", "intimider", "terroriser",
    "suspecter", "soupçonner", "incriminer",
    "ennemi", "ennemie", "adversaire", "rival", "rivale",
    "traître", "traîtresse", "danger", "menace",
    "haine", "hostilité", "conflit", "guerre",
    "mort", "meurtre", "crime", "trahison",
    "suspicion", "méfiance", "complot", "conspiration",
})

_POSITIVE_ADJ: frozenset[str] = frozenset({
    "heureux", "heureuse", "content", "contente", "joyeux", "joyeuse",
    "satisfait", "satisfaite", "reconnaissant", "reconnaissante",
    "bienveillant", "bienveillante", "généreux", "généreuse",
    "gentil", "gentille", "aimable", "sympathique", "chaleureux",
    "chaleureuse", "sincère", "honnête", "fiable", "rassurant", "rassurante",
})

_NEGATIVE_ADJ: frozenset[str] = frozenset({
    "furieux", "furieuse", "hostile", "agressif", "agressive",
    "cruel", "cruelle", "violent", "violente", "dangereux", "dangereuse",
    "méfiant", "méfiante", "soupçonneux", "soupçonneuse",
    "effrayé", "effrayée", "terrifié", "terrifiée", "coupable",
    "menaçant", "menaçante", "froid", "froide", "glacial", "glaciale",
})

_NEGATION_WORDS: frozenset[str] = frozenset({
    "ne", "n'", "pas", "jamais", "plus", "rien", "personne",
    "ni", "non", "sans", "guère", "nullement", "aucun", "aucune",
})

_WEIGHT_VERB  = 2.0
_WEIGHT_ADJ   = 0.8
_WEIGHT_SPACY = 2.5


# =============================================================================
# SCORING LEXICAL
# =============================================================================

def _score_context_lexical(tokens: List[str], start: int, end: int) -> float:
    tl = [_normalize(t) for t in tokens]
    score = 0.0
    for i in range(start, min(end, len(tokens))):
        t   = tl[i]
        neg = _is_negated(tl, i)
        for cand in _lemmatize_simple(t):
            if cand in _POSITIVE_VERBS:
                score += _WEIGHT_VERB * (-1 if neg else 1); break
            if cand in _NEGATIVE_VERBS:
                score += _WEIGHT_VERB * (1 if neg else -1); break
            if cand in _POSITIVE_ADJ:
                score += _WEIGHT_ADJ * (-1 if neg else 1); break
            if cand in _NEGATIVE_ADJ:
                score += _WEIGHT_ADJ * (1 if neg else -1); break
    return score


def _score_context_spacy(text: str) -> float:
    try:
        from .spacy_helper import get_nlp
        nlp = get_nlp()
    except Exception:
        return 0.0
    doc   = nlp(text[:500])
    score = 0.0
    for token in doc:
        lemma   = _normalize(token.lemma_ if token.lemma_ else token.text)
        has_neg = any(
            child.dep_ in ("neg", "advmod") and _normalize(child.text) in _NEGATION_WORDS
            for child in token.children
        )
        for cand in [lemma] + _lemmatize_simple(lemma):
            if cand in _POSITIVE_VERBS:
                score += _WEIGHT_SPACY * (-1 if has_neg else 1); break
            if cand in _NEGATIVE_VERBS:
                score += _WEIGHT_SPACY * (1 if has_neg else -1); break
    return score


def _score_single(tokens: List[str], pos_a: int, pos_b: int, window: int) -> float:
    left  = max(0, min(pos_a, pos_b) - window)
    right = min(len(tokens), max(pos_a, pos_b) + window + 1)
    lex   = _score_context_lexical(tokens, left, right)
    text  = " ".join(tokens[min(pos_a, pos_b): max(pos_a, pos_b) + 1])
    spa   = _score_context_spacy(text)
    return lex + spa


# =============================================================================
# AGRÉGATION
# =============================================================================

def _aggregate(scores: List[float], prior: int = 0) -> int:
    """Agrège des scores bruts en polarité finale, en utilisant le prior si signal faible."""
    if not scores:
        return prior
    n         = len(scores)
    mean      = sum(scores) / n
    pos_count = sum(1 for s in scores if s > 0.3)
    neg_count = sum(1 for s in scores if s < -0.3)

    if mean > THRESHOLD_MEAN and pos_count / n >= THRESHOLD_RATIO:
        local = 1
    elif mean < -THRESHOLD_MEAN and neg_count / n >= THRESHOLD_RATIO:
        local = -1
    else:
        local = 0

    # Si le signal local est nul → utiliser le prior (JSON ou registre livre)
    return prior if local == 0 and prior != 0 else local


def _names_match(n1: str, n2: str) -> bool:
    """
    Vérifie si deux noms normalisés correspondent,
    même si l'un est une forme courte de l'autre.
    Ex : "dors" ↔ "dors venabili", "r. daneel" ↔ "r. daneel olivaw"
    """
    if n1 == n2:
        return True
    # n1 est un préfixe/suffixe de n2 ou vice-versa
    return n2.startswith(n1 + " ") or n1.startswith(n2 + " ")


def _get_prior(a: str, b: str) -> int:
    """
    Prior en deux niveaux :
    1. JSON (paires connues ou déjà apprises) — recherche exacte puis partielle
    2. Registre livre (scores accumulés sur les chapitres précédents)
    """
    key = _make_key(a, b)
    na, nb = _normalize(a), _normalize(b)

    # Niveau 1a : correspondance exacte
    if key in _known_pairs:
        return _known_pairs[key]

    # Niveau 1b : correspondance partielle (dors ↔ dors venabili, etc.)
    for (ka, kb), pol in _known_pairs.items():
        if (_names_match(ka, na) and _names_match(kb, nb)) or            (_names_match(ka, nb) and _names_match(kb, na)):
            return pol

    # Niveau 2 : registre livre
    book_scores = _book_scores.get(key, [])
    if book_scores:
        return _aggregate(book_scores)

    return 0


def _is_already_known(a: str, b: str) -> bool:
    """
    Vérifie si une paire est déjà connue (exacte ou partielle).
    Évite les doublons lors de l'auto-enrichissement.
    """
    key = _make_key(a, b)
    if key in _known_pairs:
        return True
    na, nb = _normalize(a), _normalize(b)
    for (ka, kb) in _known_pairs:
        if (_names_match(ka, na) and _names_match(kb, nb)) or            (_names_match(ka, nb) and _names_match(kb, na)):
            return True
    return False


# =============================================================================
# INTERFACE PRINCIPALE
# =============================================================================

def score_pair_polarity(
    tokens: List[str],
    occurrences_a: List[int],
    occurrences_b: List[int],
    name_a: str = "",
    name_b: str = "",
    window: int = 25,
) -> int:
    """
    Calcule la polarité pour une paire dans un chapitre.
    Utilise le JSON et le registre livre comme prior.
    Auto-enrichit le JSON si le signal est suffisamment fort.
    """
    scores = [
        _score_single(tokens, pa, pb, window)
        for pa in occurrences_a
        for pb in occurrences_b
        if abs(pa - pb) <= window
    ]

    prior = _get_prior(name_a, name_b)
    pol   = _aggregate(scores, prior)

    # Enregistrer dans le registre livre
    key = _make_key(name_a, name_b)
    _book_scores[key].extend(scores)

    # Auto-enrichissement : signal fort + paire pas encore dans le JSON
    if scores and not _is_already_known(name_a, name_b):
        mean = sum(scores) / len(scores)
        if abs(mean) >= AUTO_SAVE_THRESHOLD:
            learned_pol = 1 if mean > 0 else -1
            _newly_learned[key] = learned_pol
            Logger.info(
                f"Auto-appris : [{name_a}] ↔ [{name_b}] = {learned_pol:+d} "
                f"(mean={mean:.2f})"
            )

    Logger.debug(
        f"[{name_a}]↔[{name_b}] n={len(scores)} "
        f"mean={sum(scores)/max(len(scores),1):.2f} "
        f"prior={prior:+d} → {pol:+d}"
    )
    return pol


def compute_signed_links(
    characters: List[str],
    tokens: List[str],
    name_to_parts: Dict[str, List[str]],
    raw_links: List[Tuple[str, str]],
    window: int = 25,
) -> Dict[Tuple[str, str], int]:
    """
    Calcule la polarité pour toutes les paires d'un chapitre.
    Met à jour le registre et peut enrichir le JSON.
    """
    from .lien_personnage import find_occurrences_multi

    occ_map = {
        name: find_occurrences_multi(tokens, name_to_parts[name])
        for name in characters if name in name_to_parts
    }

    pairs  = set(tuple(sorted((a, b))) for a, b in raw_links)
    result: Dict[Tuple[str, str], int] = {}

    for a, b in pairs:
        occ_a = occ_map.get(a, [])
        occ_b = occ_map.get(b, [])
        if occ_a and occ_b:
            pol = score_pair_polarity(tokens, occ_a, occ_b, a, b, window)
            result[(a, b)] = pol
            Logger.info(f"Polarité [{a}] ↔ [{b}] : {pol:+d}")

    return result


# Charger le JSON au démarrage du module
load_pairs()