import json
import argparse
from word_type import TokenType, NounType

    
def count_occurrences(data):
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

def main():
    parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
    parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
    args = parser.parse_args()

    with open(f"{args.input_file}", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    word_count = count_occurrences(data)

    with open(f"{args.input_file.replace('.parsed.json', '.wordcount.json')}", "w", encoding="utf-8") as f:
        json.dump(word_count, f, ensure_ascii=False, indent=4)
    print(f"Word counts written to output/{args.input_file.replace('.parsed.json', '.wordcount.json')}")



if __name__ == "__main__":
    main()