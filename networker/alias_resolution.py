from gamuLogger import Logger

def match_scores(name1: str, name2: str) -> float:
    """
    Compute a match score between two names.
    the score is a number between 0 and 1, the higher mean the names are probably aliases.
    """
    name1_parts = set(name1.lower().split())
    name2_parts = set(name2.lower().split())
    common_parts = name1_parts.intersection(name2_parts)
    total_parts = name1_parts.union(name2_parts)
    if not total_parts:
        return 0.0
    return len(common_parts) / len(total_parts)


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
            if score >= 0.5:
                Logger.trace(f"Alias match: '{persons[i]}' and '{persons[j]}' with score {score}")
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
