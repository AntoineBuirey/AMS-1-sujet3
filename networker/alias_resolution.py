from gamuLogger import Logger


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
    


def match_scores(name1: str, name2: str) -> float:
    """
    Compute a match score between two names.
    the score is a number between 0 and 1, the higher mean the names are probably aliases.
    """
    Logger.trace(f"Matching '{name1}' against '{name2}'")
    name1_parts = name1.lower().split()
    name2_parts = name2.lower().split()
    
    Logger.trace(f"Parts: {name1_parts} vs {name2_parts}")
    
    if name1.lower() in name2_parts or name2.lower() in name1_parts:
        Logger.trace("One name is a part of the other, score: 1.0")
        return 1.0
    
    if not name1_parts or not name2_parts:
        Logger.trace("One of the names has no parts, score: 0.0")
        return 0.0
    scores = []
    for part1 in name1_parts:
        best_score = 0.0
        for part2 in name2_parts:
            score = part_score(part1, part2)
            if score > best_score:
                best_score = score
        scores.append(best_score)
    final_score = sum(scores) / len(scores)
    Logger.trace(f"Final score: {final_score}")
    return final_score


def resolve_aliases(persons : list[str]) -> list[list[str]]:
    """
    Resolve aliases from a list of person names.
    Return a list of lists of aliases.
    """
    aliases : list[tuple[str, str]] = []
    n = len(persons)
    for i in range(n):
        for j in range(i + 1, n):
            score = match_scores(persons[i], persons[j])
            Logger.trace(f"Comparing '{persons[i]}' and '{persons[j]}', score: {score}")
            if score >= 0.75:
                aliases.append((persons[i], persons[j]))
    
    # Build groups of aliases
    alias_groups : list[set[str]] = []
    for alias1, alias2 in aliases:
        found_group = None
        for group in alias_groups:
            if alias1 in group or alias2 in group:
                if found_group is None:
                    found_group = group
                    group.add(alias1)
                    group.add(alias2)
                else:
                    found_group.update(group)
                    alias_groups.remove(group)
        if found_group is None:
            alias_groups.append(set([alias1, alias2]))
        
    # add singletons
    for person in persons:
        if not any(person in group for group in alias_groups):
            alias_groups.append(set([person]))
        
    return [list(group) for group in alias_groups]


if __name__ == "__main__":
    from gamuLogger import Levels
    Logger.set_level("stdout", Levels.TRACE)
    test_persons = [
        "r.daneel",
        "daneel",
        "julius",
        "enderby",
        "julius enderby",
        "baley",
        "lije",
        "le commissaire",
        "simpson",
        "vince barrett",
        "r. sammy",
        "spacetown",
        "jacques",
        "r. daneel",
        "boris",
        "elijah",
        "hari",
        "seldon",
        "hari seldon",
        "chetter hummin",
        "hummin",
        "sire",
        "demerzel",
        "historienne",
        "chetter",
        "cléon",
        "hélicon"
    ]
    resolved_aliases = resolve_aliases(test_persons)
    for group in resolved_aliases:
        print(group)