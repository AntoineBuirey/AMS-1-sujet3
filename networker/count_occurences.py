from .word_type import TokenType, NounType

    
def count_occurrences(data) -> dict[str, int]:
    word_count = {}
    for sentence in data:
        for word_info in sentence["words"]:
            if word_info['type'] in {TokenType.PROPER_NOUN, TokenType.COMMON_NOUN} \
            and word_info["noun_type"] == NounType.PERSON:
                word : str = word_info["word"]
                # word = word.capitalize()
                if word in word_count:
                    word_count[word] += 1
                else:
                    word_count[word] = 1

    # Sort by decreasing count
    return  dict(sorted(word_count.items(), key=lambda item: item[1], reverse=True))
