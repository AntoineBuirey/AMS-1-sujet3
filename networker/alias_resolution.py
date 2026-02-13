from gamuLogger import Logger
import json
import os
import re

# Chemin vers ton fichier JSON contenant les listes d'alias
ALIAS_MAP_PATH = "networker/data/alias_map.json"

def part_score(part1: str, part2: str) -> float:
    """
    Compute a score between two name parts.
    the score is a number between 0 and 1, the higher mean the parts are probably the same.
    Using the Levenshtein distance to compute the score.
    """
    if part1 == part2:
        return 1.0
    # Compute Levenshtein distance
    len1, len2 = len(part1), len(part2)
    if len1 == 0:
        return 0.0
    if len2 == 0:
        return 0.0
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if part1[i - 1] == part2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1,      # deletion
                           dp[i][j - 1] + 1,      # insertion
                           dp[i - 1][j - 1] + cost) # substitution
    distance = dp[len1][len2]
    max_len = max(len1, len2)
    return (max_len - distance) / max_len
    



# =========================
# Normalisation
# =========================

def normalize_name(name: str) -> str:
    """
    Normalise un nom pour la comparaison :
    - minuscules
    - remplace "_" par espace
    - supprime la ponctuation
    - réduit les espaces multiples
    """
    if not name:
        return ""
    name = name.lower().replace("_", " ")
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

# =========================
# Chargement des Alias Manuels
# =========================

def load_alias_map() -> list[list[str]]:
    """
    Charge les groupes d'alias manuels depuis data/alias_map.json
    """
    if not os.path.exists(ALIAS_MAP_PATH):
        Logger.warning(f"Fichier d'alias non trouvé : {ALIAS_MAP_PATH}")
        return []

    try:
        with open(ALIAS_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            # On normalise chaque nom dans les groupes pour assurer la correspondance
            return [
                [normalize_name(name) for name in group]
                for group in data
                if isinstance(group, list) and group
            ]
        return []

    except Exception as e:
        Logger.error(f"Erreur lors du chargement de l'alias map : {e}")
        return []

# =========================
# Logique de Résolution
# =========================

def resolve_aliases(persons: list[str]) -> list[list[str]]:
    """
    Prend une liste de noms de personnages et regroupe les alias.
    """
    manual_groups = load_alias_map()
    normalized_persons = [normalize_name(p) for p in persons]
    alias_pairs = []

    # 1. Identifier les paires d'alias
    for i, name1 in enumerate(persons):
        norm1 = normalized_persons[i]
        for j in range(i + 1, len(persons)):
            name2 = persons[j]
            norm2 = normalized_persons[j]

            # --- ÉTAPE A : VÉRIFICATION MANUELLE (Priorité) ---
            is_manual_match = False
            for group in manual_groups:
                if norm1 in group and norm2 in group:
                    alias_pairs.append((name1, name2))
                    is_manual_match = True
                    break
            
            if is_manual_match:
                continue # On passe au couple suivant, on ignore les règles auto

            # --- ÉTAPE B : SÉCURITÉ (Prevent weak matches) ---
            # On ne fusionne pas automatiquement deux noms d'un seul mot 
            # (sauf s'ils étaient dans la liste manuelle ci-dessus)
            if len(norm1.split()) == 1 and len(norm2.split()) == 1:
                continue

            # --- ÉTAPE C : SIMILARITÉ AUTOMATIQUE (Optionnel) ---
            # Ici tu peux ajouter ton calcul de score (ex: Levenshtein ou Jaro-Winkler)
            # score = match_scores(norm1, norm2)
            # if score >= 0.75:
            #     alias_pairs.append((name1, name2))

    # 2. Construire les groupes finaux à partir des paires
    final_groups: list[set[str]] = []

    # D'abord, on initialise les groupes avec tes listes manuelles
    # pour être sûr qu'ils existent même si certains noms ne sont pas dans le texte
    for m_group in manual_groups:
        # On ne garde que les noms qui sont réellement présents dans 'persons'
        existing_in_text = {p for p, n in zip(persons, normalized_persons) if n in m_group}
        if existing_in_text:
            final_groups.append(existing_in_text)

    # Ensuite on ajoute les paires détectées (auto ou manuelles)
    for a1, a2 in alias_pairs:
        found_group = None
        for group in final_groups:
            if a1 in group or a2 in group:
                if found_group is None:
                    group.update([a1, a2])
                    found_group = group
                else:
                    # Fusion de deux groupes si une liaison est trouvée
                    found_group.update(group)
                    final_groups.remove(group)
        
        if found_group is None:
            final_groups.append({a1, a2})

    # Ajouter les personnages isolés (singletons)
    for person in persons:
        if not any(person in group for group in final_groups):
            final_groups.append({person})

    # Convertir en liste de listes pour le retour
    return [list(group) for group in final_groups]