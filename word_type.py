from enum import StrEnum
import string
from typing import Any
from verbs_engine import VerbTree, VerbData, Pronoun, pronoun_map, Mood
from utils import Cache
from standardizer import trim_punctuation

verb_tree = VerbTree.load("verb.data")


DETERMINERS = ["le", "la", "les", "un", "une", "des", "du", "l'", "tout", "toute", "tous", "toutes"]

DETERMINER_SUFFIXES = [
    "-le", "-la", "-les", "-un", "-une", "-des", "-du", "-l'", "-il", "-elle", "-ils", "-elles",
    "-vous", "-nous", "-mon", "-ma", "-mes", "-ton", "-ta", "-tes", "-son", "-sa", "-ses",
    "-notre", "-nos", "-votre", "-vos", "-ce", "-cette", "-ces", "-y"
]

PRONOUNS = [
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
    "me", "te", "se", "moi", "toi", "lui", "eux",
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
    "notre", "nos", "votre", "vos",
    "ce", "cette", "ces",
    "on"
]

PRONOUN_PREFIXES = ["J'", "C'", "L'", "Jusqu'", "D'", "Qu'", "N'", "S'"]

ADVERBS = [
    "aujourd'hui", "d'abord", "difficilement", "doute",
    "lentement", "là-bas", "part", "peut-être",
    "vite", "oh", "aussi", "naturellement", "jamais",
    "n'", "pas", "plus", "trop", "très", "bien",
    "mal", "souvent", "toujours", "hier", "demain",
    "ici", "là", "ailleurs", "partout", "dedans", "dehors",
    "oui", "non", "peu", "beaucoup", "décidément", "ensemble",
    "doucement", "exactement", "finalement", "franchement",
    "heureusement", "impossible", "incroyablement", "lentement",
    "probablement", "rapidement", "sérieusement", "simplement",
    "soudain", "surtout", "vraiment"
]

PREPOSITIONS = [
    # Prépositions de base (avec leurs élisions)
    "à",      # La préposition simple
    "de",     # La préposition simple
    "d'",     # Élision de "de" (ex: d'Evan)
    "dans",
    "en",
    "pour",
    "par",
    "sur",
    "avec",
    "sans",
    "sous",
    
    # Formes contractées de "à" et "de"
    "au",     # Contraction de "à le"
    "aux",    # Contraction de "à les"
    "du",     # Contraction de "de le"
    "des",    # Contraction de "de les"
    
    # Autres prépositions simples
    "après",
    "avant",
    "chez",
    "contre",
    "devant",
    "derrière",
    "depuis",
    "entre",
    "vers",
    "jusque",
    "jusqu'", # Élision de "jusque" (ex: jusqu'à)
    "selon",
    "sauf"
]

LOCATION_PREPOSITIONS = [
    "à", "dans", "en", "au", "aux", "du", "des", "chez", "vers", "jusque", "jusqu'"
]
TIME_PREPOSITIONS = [
    "avant", "après", "depuis", "entre", "jusque", "jusqu'"
]
PERSON_PREPOSITIONS = [
    "chez", "avec", "contre", "selon"#, "pour"
]

CONJUNCTIONS = [
    # coordinating conjunctions
    "et",
    "ou",
    "mais",
    "donc",
    "or",
    "ni",
    "car",
    # subordinating conjunctions
    "si",
    "que",
    "lorsque",
    "quand",
    "comme",
    "puisque",
    "bien que",
    "quoique",
    "afin que",
    "pour que",
    "avant que",
    "après que",
    "tandis que",
    "pendant que",
    "aussi longtemps que",    
]

INTERJECTIONS = [
    "ah", "oh", "eh", "ouf", "hélas", "zut", "bravo", "chut", "hé", "hi", "ha"
]

PUNCTUATIONS = string.punctuation + "«»“”‘’…—–"

class TokenType(StrEnum):
    PROPER_NOUN = "proper_noun"
    COMMON_NOUN = "common_noun"
    ADJECTIVE = "adjective"
    VERB = "verb"
    ADVERB = "adverb"
    DETERMINER = "determiner"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PUNCTUATION = "punctuation"
    INTERJECTION = "interjection"
    UNKNOWN = "unknown"
    

MUST_BE_CONCATENATED = { # if multiple tokens of the same type and the type is in this set, they must be concatenated in one token
    TokenType.PROPER_NOUN,
    TokenType.COMMON_NOUN,
    TokenType.VERB,
    TokenType.ADVERB,
    TokenType.DETERMINER,
    TokenType.PRONOUN,
    TokenType.PREPOSITION,
    TokenType.CONJUNCTION,
}


class NounType(StrEnum):
    PLACE = "place"
    PERSON = "person"
    UNKNOWN = "unknown"


def is_pronoun(word : str) -> bool:
    """
    Check if a word is a pronoun (personal, reflexive, possessive, demonstrative).
    """
    w = word.lower()
    return w in PRONOUNS or any(word.startswith(prefix) for prefix in PRONOUN_PREFIXES)

def is_verb(word : str) -> bool:
    """
    Check if a word is a verb using the VerbTree.
    """
    return verb_tree.search(word.lower().strip(string.punctuation))

def is_adverbe(word : str) -> bool:
    """
    Check if a word is an adverb.
    """
    return word.lower() in ADVERBS

def is_determinant(word : str) -> bool:
    """
    Check if a word is a determinant (article, demonstrative, possessive).
    """
    return word.lower() in DETERMINERS or any(word.lower().endswith(suffix) for suffix in DETERMINER_SUFFIXES)

def is_preposition(word : str) -> bool:
    """
    Check if a word is a preposition.
    """
    return word.lower() in PREPOSITIONS

def is_conjunction(word : str) -> bool:
    """
    Check if a word is a conjunction.
    """
    return word.lower() in CONJUNCTIONS

def is_acronym(word: str) -> bool:
    """Token with 2+ letters and all letters uppercase."""
    alpha = ''.join(ch for ch in word if ch.isalpha())
    return len(alpha) >= 2 and alpha.isupper()

def is_punctuation(word: str) -> bool:
    """Check if the token is purely punctuation."""
    return all(ch in PUNCTUATIONS for ch in word) and len(word) > 0

def is_interjection(word: str) -> bool:
    """Check if the token is an interjection."""
    return word.lower() in INTERJECTIONS

def is_adjective(word: str) -> bool:
    """Check if the token is an adjective (simple heuristic)."""
    return word.lower() in get_adj_list()

@Cache
def get_fonctional_words() -> list[str]:
    """
    Return functional words (determiners, pronouns, adverbs, etc.)
    loaded from predefined local files.
    """
    words : list[str] = []
    files = ["fonctionnels_fr.txt", "verbes.txt"]
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            words += f.read().splitlines()
    return [word.lower() for word in words if not word.startswith("#") and word.strip() != ""]

@Cache
def get_adj_list() -> set[str]:
    """Return a set of known adjectives from the french_adjectives.txt file."""
    adjectives = set()
    with open("french_adjectives.txt", "r", encoding="utf-8") as f:
        for line in f:
            adj = line.strip()
            if adj:
                adjectives.add(adj.lower())
    return adjectives

def guess_type_of_token(sentence : list[str], index : int) -> TokenType:
    """Guess the type of a token (proper noun, common noun, verb, adverb, determinant, pronoun, unknown)."""
    word = sentence[index]
    if not word:
        return TokenType.UNKNOWN
    if is_determinant(word):
        return TokenType.DETERMINER
    if is_pronoun(word):
        return TokenType.PRONOUN
    if is_adverbe(word):
        return TokenType.ADVERB
    if is_verb(word):
        return TokenType.VERB
    if is_preposition(word):
        return TokenType.PREPOSITION
    if is_conjunction(word):
        return TokenType.CONJUNCTION
    if is_punctuation(word):
        return TokenType.PUNCTUATION
    if is_interjection(word):
        return TokenType.INTERJECTION
    if is_adjective(word):
        return TokenType.ADJECTIVE
    if word[0].isupper():
        if len(word) == 1:
            return TokenType.UNKNOWN
        if index == 0:
            normalized_word = trim_punctuation(word)
            # First word of the sentence
            if any(char in word for char in string.ascii_letters):  # contains at least one letter
                if (normalized_word not in get_fonctional_words()):
                    return TokenType.PROPER_NOUN
        else:
            return TokenType.PROPER_NOUN
    
    return TokenType.COMMON_NOUN

def _neighbor_normalized(tokens: list[str], index: int, offset: int) -> str:
    """Return normalized neighbor token or empty string if out of bounds."""
    pos = index + offset
    if 0 <= pos < len(tokens):
        return trim_punctuation(tokens[pos])
    return ""


def classify_token_with_context(
    sentence_tokens: list[str],
    index: int,
    all_caps: bool,
    promoted_tokens: set | None = None,
    promoted_bigrams: set | None = None,
    auto_demote_tokens: set | None = None,
) -> TokenType:
    """
    Context-aware token classifier.

    Parameters
    - sentence_tokens: list of tokens for the sentence
    - index: index of token to classify
    - all_caps: precomputed flag meaning "sentence mostly uppercase"
    - promoted_tokens: set of normalized tokens known to be proper (optional)
    - promoted_bigrams: set of normalized bigrams (tuples) known to be proper (optional)
    - auto_demote_tokens: set of normalized tokens known to be common (optional)

    Returns a TokenType. Behaviour:
    - Performs functional/lexical checks first (determiner/pronoun/adverb/verb).
    - If not ALL-CAPS, delegates to `guess_type_of_token` (surface heuristics).
    - If ALL-CAPS, applies heuristics:
        - acronyms => PROPER_NOUN
        - tokens in auto_demote_tokens => COMMON_NOUN
        - tokens in promoted_tokens => PROPER_NOUN
        - tokens part of promoted_bigrams (prev/current or current/next) => PROPER_NOUN
        - otherwise => COMMON_NOUN
    """
    word = sentence_tokens[index]

    # Non ALL-CAPS: use the existing surface-level guesser
    if not all_caps:
        return guess_type_of_token(sentence_tokens, index)

    # Use empty sets if none provided (no globals needed)
    promoted_tokens = promoted_tokens or set()
    promoted_bigrams = promoted_bigrams or set()
    auto_demote_tokens = auto_demote_tokens or set()

    normalized_word = trim_punctuation(word)

    if normalized_word in auto_demote_tokens:
        return TokenType.COMMON_NOUN

    if normalized_word in promoted_tokens:
        return TokenType.PROPER_NOUN

    prev = _neighbor_normalized(sentence_tokens, index, -1)
    nxt = _neighbor_normalized(sentence_tokens, index, 1)
    if (normalized_word, nxt) in promoted_bigrams or (prev, normalized_word) in promoted_bigrams:
        return TokenType.PROPER_NOUN

    return TokenType.COMMON_NOUN


PRONOUN_MAP = {
    "je": Pronoun.JE,
    "tu": Pronoun.TU,
    "il": Pronoun.IL_ELLE_ON,
    "elle": Pronoun.IL_ELLE_ON,
    "on": Pronoun.IL_ELLE_ON,
    "nous": Pronoun.NOUS,
    "vous": Pronoun.VOUS,
    "ils": Pronoun.ILS_ELLES,
    "elles": Pronoun.ILS_ELLES
}

def get_verb_data(verb: str, words_list_dict, position : int) -> VerbData:
    """Return all possible conjugations and info for a verb as a list of VerbData."""
    candidates = verb_tree.get(verb.lower().strip(string.punctuation))
    if not candidates:
        if " " in verb:
            part1, part2 = verb.split(" ", 1)
            # if part2 is at the infinitive, try to get the verb data for part1 only
            part2_data = verb_tree.get(part2.lower().strip(string.punctuation))
            if part2_data and any(vd.mood == Mood.INFINITIF for vd in part2_data):
                candidates = verb_tree.get(part1.lower().strip(string.punctuation))
        else:
            raise ValueError(f"Verb '{verb}' not found in verb tree.")
    if not candidates:
        raise ValueError(f"Verb '{verb}' not found in verb tree.")
    if len(candidates) == 1:
        return candidates[0]
    else:
        # If multiple candidates, try to disambiguate using context
        # (simple heuristic: check previous word for pronoun)
        if position > 0:
            prev_word = words_list_dict[-1]["word"].lower()
            if prev_word in PRONOUN_MAP:
                pronoun = PRONOUN_MAP[prev_word]
                filtered = [vd for vd in candidates if vd.pronoun == pronoun]
                if filtered:
                    return filtered[0]
        # If still ambiguous, return the first candidate
        print(f"Warning: Ambiguous verb '{verb}' with multiple candidates. Returning the first one.")
        print(f"Candidates:\n\t{"\n\t".join(str(c) for c in candidates)}")
        return candidates[0]


def merge_tokens(tokens: list[str], start: int, end: int) -> str:
    """Merge tokens from start to end (inclusive) into a single token with spaces."""
    return " ".join(tokens[start:end+1])





PLACE_DETERMINERS = [
    "à", "de", "en", "au", "aux", "du", "des", "dans", "vers", "chez"
]
PERSON_DETERMINERS = [
    "m.", "mme", "dr", "prof", "monsieur", "madame", "mademoiselle"
]


def guess_noun_type_old(sentence : list[str], sentence_data : list[dict[str, int|str|Any]], index : int, word_type : TokenType) -> NounType:
    """
    Guess the type of a noun (place, person, unknown).
    It will be based on simple heuristics : 
    - if the previous word is a determinant of place (à, de, en, au, aux, du, des, dans, vers, chez), it's a place
    - if the previous word is a determinant of person (M., Mme, Dr, Prof, monsieur), it's a person
    - if the previous word is another determinant, check the one before
    - if the word is at the beginning of the sentence and its a proper noun, it's most likely a person
    - otherwise, return UNKNOWN
    """
    if index == 0 and word_type == TokenType.PROPER_NOUN:
        # First word of the sentence and proper noun
        return NounType.PERSON
    
    if index-1 >= len(sentence_data) or index == 0:
        # no previous word, cannot determine
        return NounType.UNKNOWN
    
    # if the word before is a preposition and we have a proper noun, it's most likely a place
    # if it's a verb, it's most likely a person
    # Je vais à Paris -> Paris is a place
    # Il rencontre Marie -> Marie is a person
    if sentence_data[index-1]["type"] == TokenType.PREPOSITION:
        if word_type == TokenType.PROPER_NOUN:
            return NounType.PLACE
    if sentence_data[index-1]["type"] == TokenType.VERB:
        return NounType.PERSON

    if sentence_data[index-1]["type"] == TokenType.DETERMINER:
        step_back = 2
    else:
        step_back = 1

    prev_word = sentence[index - step_back].lower()
    prev_word_data = sentence_data[index - step_back]
    
    if prev_word_data["type"] == TokenType.VERB:
        verb_data : dict = prev_word_data["verb_data"] # type: ignore
        # if the previous word is a verb at the simple past tense, at the third person singular, it's most likely a person
        if verb_data['tense'] == "passé simple" and verb_data['pronoun'] == "il/elle/on" :
            return NounType.PERSON
    
    if prev_word in PLACE_DETERMINERS and word_type == TokenType.PROPER_NOUN:
        # Previous word is a place determiner, it's a place (only for proper nouns because common nouns can be anything)
        return NounType.PLACE
    if prev_word in PERSON_DETERMINERS:
        # Previous word is a person determiner, it's a person
        return NounType.PERSON
    return NounType.UNKNOWN


def guess_noun_type(sentence : list[str], sentence_data : list[dict[str, int|str|Any]], index : int, word_type : TokenType) -> NounType:
    if word_type == TokenType.PROPER_NOUN:
        # if the word is at the beginning of the sentence, it's most likely a person
        if index == 0:
            return NounType.PERSON
        
        #check if the previous word is a determiner of place or person
        previous_word = sentence[index-1].lower()
        previous_word_data = sentence_data[-1]
        if previous_word in PLACE_DETERMINERS:
            return NounType.PLACE
        if previous_word in PERSON_DETERMINERS:
            return NounType.PERSON
        if previous_word_data["type"] == TokenType.DETERMINER:
            #in that case check the word before
            # ex: le Dr. Smith -> Smith is a person
            if index-2 >= 0:
                previous_previous_word = sentence[index-2].lower()
                if previous_previous_word in PLACE_DETERMINERS:
                    return NounType.PLACE
                if previous_previous_word in PERSON_DETERMINERS:
                    return NounType.PERSON
        if previous_word_data["type"] == TokenType.VERB:
            # if the previous word is a verb, it's most likely a person
            # ex: Il rencontre Marie -> Marie is a person
            return NounType.PERSON
        if previous_word in LOCATION_PREPOSITIONS:
            return NounType.PLACE
        if previous_word in PERSON_PREPOSITIONS:
            return NounType.PERSON
        
        # otherwise unknown
        return NounType.UNKNOWN
    
    elif word_type == TokenType.COMMON_NOUN:
        # check for prepositions and verbs before the noun
        if index == 0:
            return NounType.UNKNOWN
        previous_word = sentence[index-1].lower()
        previous_word_data = sentence_data[-1]
        if previous_word_data["type"] == TokenType.PREPOSITION:
            # in that case check if it's a location or person preposition
            # ex: à Paris -> Paris is a place
            return NounType.UNKNOWN
        if previous_word_data["type"] == TokenType.DETERMINER:
            # in that case check words before unitl we find anything other than a determiner or an adverb
            # ex: je cherche tranquillement la maison de mon ami -> maison is a place because of "la"
            if index-2 >= 0:
                previous_previous_word = sentence[index-2].lower()
                if previous_previous_word in LOCATION_PREPOSITIONS:
                    return NounType.PLACE
                if previous_previous_word in PERSON_PREPOSITIONS:
                    return NounType.PERSON
        
        return NounType.UNKNOWN
    else:
        raise ValueError(f"Cannot guess noun type for word type {word_type}")