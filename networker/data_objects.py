from dataclasses import dataclass

from .token_type import TokenType, NounType
from .verbs_engine import Mood, Tense, Pronoun

class DataObject:
    
    class Unknown: ...

    @dataclass(eq=False)
    class Word:
        word: str
        position: int

        def __eq__(self, other):
            if not isinstance(other, DataObject.Word):
                return NotImplemented
            return self.word == other.word

        def __hash__(self):
            return hash(self.word)

        def to_dict(self):
            return {
                "word": self.word,
                "position": self.position
            }
        

    class Adjective(Word): ...
    class Adverb(Word): ...
    class Determiner(Word): ...
    class Preposition(Word): ...
    class Conjunction(Word): ...
    class Punctuation(Word): ...
    class Interjection(Word): ...
    class Acronym(Word): ...

    class Verb(Word):
        infinitive: str
        mood: Mood
        tense: Tense
        pronoun: Pronoun
        
        def to_dict(self):
            base_dict = super().to_dict()
            base_dict.update({
                "infinitive": self.infinitive,
                "mood": self.mood.value,
                "tense": self.tense.value,
                "pronoun": self.pronoun.value
            })
            return base_dict
        
    class Noun(Word):
        noun_type: NounType
        noun_type_reason: str
        
        def to_dict(self):
            base_dict = super().to_dict()
            base_dict.update({
                "noun_type": self.noun_type.value,
                "noun_type_reason": self.noun_type_reason
            })
            return base_dict
        
    class ProperNoun(Noun): ...
    class CommonNoun(Noun): ...

    class Pronoun(Word):
        refer_to: 'DataObject.Noun|DataObject.Unknown'
        
        def to_dict(self):
            base_dict = super().to_dict()
            refer_to = getattr(self, "refer_to", DataObject.Unknown())
            base_dict.update({
                "refer_to": refer_to.word if isinstance(refer_to, DataObject.Noun) else "unknown"
            })
            return base_dict


    @staticmethod
    def build_Word(word : str, position, type: TokenType) -> Word:
        if type == TokenType.ADJECTIVE:
            return DataObject.Adjective(word, position)
        elif type == TokenType.ADVERB:
            return DataObject.Adverb(word, position)
        elif type == TokenType.DETERMINER:
            return DataObject.Determiner(word, position)
        elif type == TokenType.PREPOSITION:
            return DataObject.Preposition(word, position)
        elif type == TokenType.CONJUNCTION:
            return DataObject.Conjunction(word, position)
        elif type == TokenType.PUNCTUATION:
            return DataObject.Punctuation(word, position)
        elif type == TokenType.INTERJECTION:
            return DataObject.Interjection(word, position)
        elif type == TokenType.ACRONYM:
            return DataObject.Acronym(word, position)
        elif type == TokenType.VERB:
            # verb data will be filled later
            return DataObject.Verb(word, position)
        elif type == TokenType.PROPER_NOUN:
            # noun type and reason will be filled later
            return DataObject.ProperNoun(word, position)
        elif type == TokenType.COMMON_NOUN:
            # noun type and reason will be filled later
            return DataObject.CommonNoun(word, position)
        elif type == TokenType.PRONOUN:
            # refer_to will be filled later
            return DataObject.Pronoun(word, position)
        else:
            raise ValueError(f"Unknown token type: {type}")

    @dataclass
    class Sentence:
        index: int
        original_sentence: str
        full_sentence: str
        maybe_incomplete: bool
        page_index: int
        tokens: list[str]
        words: list['DataObject.Word']
        all_caps: bool

        def __hash__(self):
            return hash((self.index, self.original_sentence, self.page_index))
        
        def to_dict(self):
            return {
                "index": self.index,
                "original_sentence": self.original_sentence,
                "full_sentence": self.full_sentence,
                "maybe_incomplete": self.maybe_incomplete,
                "page_index": self.page_index,
                "tokens": self.tokens,
                "words": [word.to_dict() for word in self.words],
                "all_caps": self.all_caps
            }

    @dataclass
    class WordOccurence:
        quantity : int
        sentences : list['DataObject.Sentence']
        
        def __hash__(self):
            return hash((self.quantity, tuple(self.sentences)))
        
        def to_dict(self):
            return {
                "quantity": self.quantity,
                "sentences": [sentence.to_dict() for sentence in self.sentences]
            }