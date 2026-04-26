from enum import StrEnum
import string
from typing import Any
import re

from gamuLogger import Logger

from .verbs_engine import VerbTree, VerbData, Pronoun, pronoun_map, Mood, Tense
from .utils import resource, Cache
from .standardizer import trim_punctuation
from .spacy_helper import spacy_label_for_token

Logger.set_module("word_type")

verb_tree = VerbTree.load(resource("verb.data"))


def load_file(path: str) -> list[str]:
    """Load a file and return its lines as a list of strings."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    return lines


# DETERMINERS = ["le", "la", "les", "un", "une", "des", "du", "l'", "tout", "toute", "tous", "toutes"]
DETERMINERS = load_file(resource("determiner.dict.txt"))

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

ADVERBS = load_file(resource("adverb.dict.txt"))

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
    "sauf",
    "voilà"
]

LOCATION_PREPOSITIONS = [
    "à", "dans", "en", "au", "aux", "du", "des", "chez", "vers", "jusque", "jusqu'"
]

TIME_PREPOSITIONS = [
    "avant", "après", "depuis", "entre", "jusque", "jusqu'"
]


PERSON_PREPOSITIONS = [
    "chez", "selon"
]

# Special case: Encyclopaedia Galactica should never be classified as a person
SPECIAL_NON_PERSON_TOKENS = [
    "encyclopaedia",
    "galactica",
    "encyclopaedia_galactica",
    "encyclopaedia galactica",
    "mycogène",
    "terra",
    "galactica2",
    "spacetown",
    "new york city",
    "subdivisions",
    "principes",
    "désir"
]


CONJUNCTIONS = load_file(resource("conjunction.dict.txt"))

# INTERJECTIONS = ["ah", "oh", "eh", "ouf", "hélas", "zut", "bravo", "chut", "hé", "hi", "ha"]
INTERJECTIONS = load_file(resource("interjection.dict.txt"))

PUNCTUATIONS = string.punctuation + "«»“”‘’…—–"

#detect things like "R.D.T", "P.s.A", "U.S.A", "a.M", "R.G.p.D"
RE_ACRONYM = re.compile(r"^([A-Za-z]\.){2,}[A-Za-z]?$")

COMMON_NOUNS = load_file(resource("noun.dict.txt"))

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
    ACRONYM = "acronym"
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


SPECIAL_PROPER_NOUNS = [
    "R."
]


# used to detect things like "monsieur le commissaire"
PLACE_DETERMINERS = [
    "à", "de", "en", "au", "aux", "du", "des", "dans", "vers", "chez"
]
PERSON_DETERMINERS = [
    "m.", "mme", "mlle", "dr", "prof", "monsieur", "madame", "mademoiselle",
    "capitaine", "colonel", "général", "lieutenant", "sergent",
    "maître", "père", "frère", "sœur", "oncle", "tante",
    "roi", "reine", "prince", "princesse", "duc", "duchesse",
    "lord", "lady", "sir", "dame"
]

# these verbs imply that a person is the next noun
VERBS_INTRODUCING_PERSONS = [
    "rencontrer", "aider", "trouver", "connaître",
    "voir", "croiser", "saluer", "nommer",
    "présenter", "interroger", "questionner", "observer", "regarder",
    "écouter", "entendre", "parler", "dire", "répondre", "demander"
]


class NounType(StrEnum):
    PLACE = "place"
    PERSON = "person"
    UNKNOWN = "unknown"

def is_acronym(word: str) -> bool:
    return bool(RE_ACRONYM.match(word))

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
    return verb_tree.search(word.lower().strip(string.punctuation), False)

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

def is_punctuation(word: str) -> bool:
    """Check if the token is purely punctuation."""
    return all(ch in PUNCTUATIONS for ch in word) and len(word) > 0

def is_interjection(word: str) -> bool:
    """Check if the token is an interjection."""
    return word.lower() in INTERJECTIONS

def is_adjective(word: str) -> bool:
    """Check if the token is an adjective (simple heuristic)."""
    return word.lower() in get_adj_list()

def is_hardcoded_proper_noun(word: str) -> bool:
    """Check if the token is a hardcoded proper noun."""
    return word in SPECIAL_PROPER_NOUNS

@Cache
def get_fonctional_words() -> list[str]:
    """
    Return functional words (determiners, pronouns, adverbs, etc.)
    loaded from predefined local files.
    """
    words : list[str] = []
    files = [resource("fonctionnels_fr.txt")]
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            words += f.read().splitlines()
    return [word.lower() for word in words if not word.startswith("#") and word.strip() != ""]

@Cache
def get_adj_list() -> set[str]:
    """Return a set of known adjectives from the french_adjectives.txt file."""
    adjectives = set()
    with open(resource("french_adjectives.txt"), "r", encoding="utf-8") as f:
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
    if is_hardcoded_proper_noun(word):
        return TokenType.PROPER_NOUN
    if word.lower() in COMMON_NOUNS:
        return TokenType.COMMON_NOUN
    if is_acronym(word):
        return TokenType.ACRONYM
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
    verb = verb.lower().strip(string.punctuation)
    candidates = verb_tree.get(verb, strict=False)
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
        Logger.debug(f"Ambiguous verb '{verb}' with multiple candidates. Returning the first one.")
        Logger.trace(f"Candidates:\n\t{"\n\t".join(str(c) for c in candidates)}")
        return candidates[0]


def merge_tokens(tokens: list[str], start: int, end: int) -> str:
    """Merge tokens from start to end (inclusive) into a single token with spaces."""
    return " ".join(tokens[start:end+1])




def guess_noun_type(sentence : list[str], sentence_data : list[dict[str, Any]], index : int, word_type : TokenType, maybe_incomplete_sentence : bool) -> tuple[NounType, str]:
    """
    return the guessed noun type (place, person, unknown) and the reason
    """
    word = sentence[index]
    normalized = trim_punctuation(word.lower())
    Logger.debug(f"Guessing noun type for '{word}' (normalized: '{normalized}') at index {index} with word type {word_type}")
    if normalized in SPECIAL_NON_PERSON_TOKENS:
        return NounType.UNKNOWN, "special non-person token"
    if word_type == TokenType.PROPER_NOUN:
        if index == 0 and not maybe_incomplete_sentence:
            # if this is the first and only word of he sentence excluding punctuation, we cannot be sure it's a person, it can be a place or something else (ex: "Hey !")
            if len(sentence) == 1 or all(is_punct for i, is_punct in enumerate(sentence) if i != index):
                return NounType.UNKNOWN, "only word of the sentence (excluding punctuation)"

            if index + 1 < len(sentence):
                next_word = sentence[index+1].lower()
                if next_word == "=":
                    return NounType.UNKNOWN, "footer detected"
            return NounType.PERSON, "first word of the sentence"
        
        #check if the previous word is a determiner of place or person
        if index > 0 and sentence_data:
            previous_word = sentence[index-1].lower()
            previous_word_data = sentence_data[-1]
            if previous_word in PLACE_DETERMINERS:
                return NounType.PLACE, "place determiner before"
            if previous_word in PERSON_DETERMINERS:
                return NounType.PERSON, "person determiner before"
            if previous_word_data["type"] == TokenType.DETERMINER.value:
                #in that case check the word before
                # ex: le Dr. Smith -> Smith is a person
                if index-2 >= 0:
                    previous_previous_word = sentence[index-2].lower()
                    if previous_previous_word in PLACE_DETERMINERS:
                        return NounType.PLACE, "place determiner two words before"
                    if previous_previous_word in PERSON_DETERMINERS:
                        return NounType.PERSON, "person determiner two words before"
            if previous_word in LOCATION_PREPOSITIONS:
                return NounType.PLACE, "location preposition before"
            if previous_word in PERSON_PREPOSITIONS:
                return NounType.PERSON, "person preposition before"
        
        # if the next word is a verb at 3rd person, it's most likely a person
        # if index + 1 < len(sentence):
        #     next_word = sentence[index+1].lower()
        #     next_word_data = guess_type_of_token(sentence, index+1)
        #     if next_word_data == TokenType.VERB:
        #         verb_data = get_verb_data(next_word, sentence_data, index+1)
        #         if verb_data.pronoun == Pronoun.IL_ELLE_ON:
        #             return NounType.PERSON, "next word is 3rd person verb"
                
        # if the previous word is a verb at 3rd person, it's most likely a person
        # but in that case, the verb should be in past tense (passé simple or imparfait)
        # in that case, they must be no subject pronoun before the verb
        if index - 1 >= 0:
            previous_word = sentence[index-1].lower()
            previous_word_data = guess_type_of_token(sentence, index-1)
            if previous_word_data == TokenType.VERB:
                verb_data = get_verb_data(previous_word, sentence_data, index-1)
                if verb_data.pronoun == Pronoun.IL_ELLE_ON and verb_data.tense in [Tense.PASSE_SIMPLE, Tense.IMPARFAIT]:
                    # return NounType.PERSON, "previous word is 3rd person past tense verb"
                    # check if there is no subject pronoun before the verb
                    has_subject_pronoun = False
                    Logger.debug(f"Checking for subject pronoun before verb '{previous_word}' at index {index-1}")
                    # locate the verb in sentence_data (may be different from index-1 due to merged tokens)
                    verb_position_in_data = None
                    for i, word_data in enumerate(sentence_data):
                        if trim_punctuation(word_data["word"]).lower() == previous_word:
                            verb_position_in_data = i
                            break
                    if verb_position_in_data is not None:
                        for j in range(verb_position_in_data-1, -1, -1):
                            word_data = sentence_data[j]
                            if word_data["type"] == TokenType.PRONOUN:
                                pronoun_word = word_data["word"].lower()
                                if pronoun_word in PRONOUN_MAP:
                                    pronoun = PRONOUN_MAP[pronoun_word]
                                    if pronoun == Pronoun.IL_ELLE_ON:
                                        has_subject_pronoun = True
                                        Logger.debug(f"Found subject pronoun '{pronoun_word}' before verb '{previous_word}'")
                                        break
                            elif word_data["type"] not in [TokenType.DETERMINER, TokenType.ADVERB]:
                                # stop searching if we hit a non-functional word
                                break
                    if not has_subject_pronoun:
                        return NounType.PERSON, "previous word is 3rd person past tense verb without subject pronoun before"
                
        # if the previous word is a verb that implies introducing a person
        if index - 1 >= 0:
            previous_word = sentence[index-1].lower()
            previous_word_data = guess_type_of_token(sentence, index-1)
            if previous_word_data == TokenType.VERB:
                verb_data = get_verb_data(previous_word, sentence_data, index-1)
                if verb_data.infinitive in VERBS_INTRODUCING_PERSONS:
                    return NounType.PERSON, "previous word is verb introducing person"
        
        # otherwise check if we encountered this token and if we know its type
        normalized_word = trim_punctuation(sentence[index])
        for i, word_data in enumerate(sentence_data):
            if i != index and trim_punctuation(word_data["word"]) == normalized_word:
                if "noun_type" in word_data:
                    return NounType(word_data["noun_type"]), f"known noun type from previous occurrence: {word_data['noun_type']}"
                
        # if the word is in uppercase, consider it as a person (his name is written somewhere, like on a door)
        # if it has at least one neighbor that is also a proper_noun uppercase
        if sentence[index].isupper():
            if (index > 0 and sentence[index-1].isupper() and guess_type_of_token(sentence, index-1) == TokenType.PROPER_NOUN) or \
               (index + 1 < len(sentence) and sentence[index+1].isupper() and guess_type_of_token(sentence, index+1) == TokenType.PROPER_NOUN):
                return NounType.PERSON, "all caps with proper noun neighbor"
            
        
        # if the word is between 2 commas or between a comma and the end of the sentence,
        # ex: ", John ," / ", John."
        if (index > 0 and sentence[index-1] == ",") and \
           (index + 1 < len(sentence) and sentence[index+1] in [",", ".", ";", "!", "?"]):
            return NounType.PERSON, "between commas or comma and sentence end"

        # --- spaCy vote (hybrid rules + NER) ---
        # Helps reduce false characters and recover missed person entities.
        spacy_label = spacy_label_for_token(sentence, index)

        # If spaCy strongly indicates a person, promote to PERSON.
        if spacy_label == "PER":
            return NounType.PERSON, "spacy vote PER"

        # If spaCy indicates a location, promote to PLACE.
        if spacy_label == "LOC":
            return NounType.PLACE, "spacy vote LOC"

        # If spaCy indicates ORG/MISC, avoid mislabeling as PERSON.
        if spacy_label in {"ORG", "MISC"}:
            return NounType.UNKNOWN, f"spacy vote {spacy_label}"

        return NounType.UNKNOWN, "no specific clues found"
    
    elif word_type == TokenType.COMMON_NOUN:
        # check for prepositions and verbs before the noun
        if index == 0:
            return NounType.UNKNOWN, "first word of the sentence"
        previous_word = sentence[index-1].lower()
        previous_word_data = sentence_data[-1]
        if previous_word_data["type"] == TokenType.PREPOSITION:
            # in that case check if it's a location or person preposition
            # ex: à Paris -> Paris is a place
            return NounType.UNKNOWN, "preposition before common noun"
        if previous_word_data["type"] == TokenType.DETERMINER:
            # in that case check words before unitl we find anything other than a determiner or an adverb
            # ex: je cherche tranquillement la maison de mon ami -> maison is a place because of "la"
            if index-2 >= 0:
                previous_previous_word = sentence[index-2].lower()
                if previous_previous_word in LOCATION_PREPOSITIONS:
                    return NounType.PLACE, "location preposition two words before"
                if previous_previous_word in PERSON_PREPOSITIONS or previous_previous_word in PERSON_DETERMINERS:
                    return NounType.PERSON, "person preposition or determiner two words before"
        
        # otherwise check if we encountered this token and if we know its type
        normalized_word = trim_punctuation(sentence[index])
        for i, word_data in enumerate(sentence_data):
            if i != index and trim_punctuation(word_data["word"]) == normalized_word:
                if "noun_type" in word_data:
                    return NounType(word_data["noun_type"]), f"known noun type from previous occurrence: {word_data['noun_type']}"
        return NounType.UNKNOWN, "no specific clues found"
    else:
        raise ValueError(f"Cannot guess noun type for word type {word_type}")


def identify_subject_for_pronoun(data : list[dict]) -> list[dict]:
    """
    Try to identify the subject for pronouns in the text.
    Add a "refer-to" field to pronoun tokens if found.
    Keep track of the last known subject (proper noun or common noun of type person).
    Only work for singular pronouns (je, tu, il, elle, on).
    Do not cross pages because we have only one page over 2, so the context is lost.
    if the subject cannot be found, leave it as unknown.
    """
    last_subjects_by_page : dict[int, str] = {}
    for sentence_data in data:
        page_index = sentence_data["page_index"]
        words_list = sentence_data["words"]
        for word_data in words_list:
            if word_data["type"] in [TokenType.PROPER_NOUN, TokenType.COMMON_NOUN]:
                if word_data.get("noun_type") == NounType.PERSON:
                    last_subjects_by_page[page_index] = word_data["word"]
            elif word_data["type"] == TokenType.PRONOUN:
                pronoun_word = word_data["word"].lower()
                if pronoun_word in ["je", "tu", "il", "elle", "on"]:
                    subject = last_subjects_by_page.get(page_index, "unknown")
                    word_data["refer-to"] = subject
    return data