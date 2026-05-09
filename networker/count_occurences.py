from typing import Any

from .word_type import TokenType, NounType
from .data_objects import DataObject as DO

    
def count_occurrences(sentences: list[DO.Sentence]) -> dict[DO.Noun, DO.WordOccurence]:
    """Count the occurrences of proper nouns and common nouns representing a person in the text.

    Args:
        sentences (list[dict]): The input data, a list of sentences, where each sentence is a dictionary containing a "words" key with a list of word information.

    Returns:
        dict[str, dict[str, int | list[int]]]: A dictionary mapping each proper noun and common noun representing a
        person to a dictionary containing the count of occurrences and the list of sentences ids where it appears
    """
    # word_count : dict[str, dict[str, int | list[int]]] = {}
    word_occurences : dict[DO.Noun, DO.WordOccurence] = {}
    for sentence in sentences:
        for word in sentence.words:
            if (isinstance(word, DO.Noun) 
            and word.noun_type == NounType.PERSON):
                if word in word_occurences:
                    word_occurences[word].quantity += 1
                    word_occurences[word].sentences.append(sentence)
                else:
                    word_occurences[word] = DO.WordOccurence(1, [sentence])

    # Sort by decreasing count
    return dict(sorted(word_occurences.items(), key=lambda item: item[1].quantity, reverse=True))
