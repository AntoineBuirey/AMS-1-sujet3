from enum import StrEnum

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
    
class NounType(StrEnum):
    PLACE = "place"
    PERSON = "person"
    UNKNOWN = "unknown"