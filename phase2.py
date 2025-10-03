import re
import nltk
import argparse
import os
import json
import string
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize

class Cache:
    _cache = {}
    
    def __init__(self, func):
        self.func = func
        
    def __call__(self, *args):
        func_cache = Cache._cache.get(self.func.__name__, {})
        if str(args) in func_cache:
            return func_cache[str(args)]
        Cache._cache[self.func.__name__] = func_cache
        result = self.func(*args)
        func_cache[str(args)] = result
        return result

class DebugFunc:
    _debug = False
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if not DebugFunc._debug:
            return self.func(*args, **kwargs)
        result = self.func(*args, **kwargs)
        print(f"Function {self.func.__name__} called with args: {args}, kwargs: {kwargs}. Result: {result}")
        return result


def split_word_with_quote(word : str) -> list[str]:
    if "'" in word:
        parts = word.split("'")
        print(f"Splitting word with quote: {word} -> {parts}")
        return [part for part in parts if part]
    return [word]

def split_words_with_quote(words : list[str]) -> list[str]:
    result = []
    for word in words:
        result.extend(split_word_with_quote(word))
    return result
    

def is_determinant(word : str) -> bool:
    determinants = ["le", "la", "les", "un", "une", "des", "du", "l'"]
    suffixes = ["-le", "-la", "-les", "-un", "-une", "-des", "-du", "-l'", "-il", "-elle", "-ils", "-elles",
                "-vous", "-nous", "-mon", "-ma", "-mes", "-ton", "-ta", "-tes", "-son", "-sa", "-ses",
                "-notre", "-nos", "-votre", "-vos", "-ce", "-cette", "-ces", "-y"]
    return word.lower() in determinants or any(word.lower().endswith(suffix) for suffix in suffixes)

@DebugFunc
def is_pronoun(word : str) -> bool:
    pronouns = ["je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
                "me", "te", "se", "moi", "toi", "lui", "eux",
                "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
                "notre", "nos", "votre", "vos",
                "ce", "cette", "ces",
                "on"
                ]
    prefixes = ["J'", "C'", "L'", "Jusqu'", "D'", "Qu'", "N'", "S'"]  

    w = word.lower()
    return w in pronouns or any(word.startswith(prefix) for prefix in prefixes)

@Cache
def is_adverbe(word : str) -> bool:
    adverbs = [
    "aujourd'hui", "d'abord", "difficilement", "doute",
        "lentement", "là-bas", "part", "peut-être",
        "vite", "oh", "aussi", "naturellement", "jamais",]
    return word.lower() in adverbs

def delete_page_numbers(text: str) -> str:
    return re.sub(r"\n� \d+ � \n", '.', text)

@DebugFunc
def is_proper_noun(sentence : list[str], index : int) -> bool:
    word = sentence[index]
    if not word[0].isupper():
        return False
    if index == 0:  # first word of the sentence and starts with a capital letter
        if any(char in word for char in string.ascii_letters):  # contains at least one letter
            return (
                word.lower() not in get_fonctional_words()
                and not is_pronoun(word)
                and not is_adverbe(word)
                and not is_determinant(word)
            )
    else:
        return True # not the first word of the sentence and starts with a capital letter
    return False


@Cache
def get_fonctional_words() -> list[str]:
    with open("fonctionnels_fr.txt", "r", encoding="utf-8") as f:
        words = f.read().splitlines()
    with open("verbes.txt", "r", encoding="utf-8") as f:
        words += f.read().splitlines()
    return [word.lower() for word in words if not word.startswith("#") and word.strip() != ""]

parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
parser.add_argument("--proper", "-p", action="store_true", help="Only keep proper nouns.")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode.")
args = parser.parse_args()

DebugFunc._debug = args.debug

with open(f"text_dataset/{args.input_file}", "r", encoding="utf-8") as f:
    text = f.read()

text = delete_page_numbers(text)
    
# same file name, but in the output folder
output_file = os.path.join("output", os.path.basename(args.input_file))
output_file = output_file.replace(".txt", ".parsed.json")

# Split text into sentences using regex to handle specific cases
# This regex splits at ., !, ? if preceded by at least two letters or a closing parenthesis or a quote
# It also splits at ... followed by space, or at quotes, or at - digit -
sentences = re.split(r'(?<=[\w )\"]{2}[.!?])|\.\.\.\ +|\"|- \d -', text)



result = []
for i in range(len(sentences)):
    sentence = sentences[i].strip(" \n\t\r-()")
    if sentence == "":
        continue

    words_list = word_tokenize(sentence, language="french")
    words_list = split_words_with_quote(words_list)
    words_list_dict = []
    for j in range(len(words_list)):
        word = words_list[j]
        is_proper = is_proper_noun(words_list, j)
        
        if is_proper and words_list_dict and words_list_dict[-1]["is_proper_noun"]:
            words_list_dict[-1]["word"] += " " + word
            continue
        else:
            words_list_dict.append({
                "word": word,
                "is_proper_noun": is_proper,
                "position" : j
            })
    if words_list_dict:
        result.append({
            "sentence_index": i,
            "full_sentence": sentence,
            "words": words_list_dict
        })

if args.proper:
    for sentence in result:
        sentence["words"] = [word for word in sentence["words"] if word["is_proper_noun"]]
    result = [sentence for sentence in result if sentence["words"]]

os.makedirs("output", exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(result, f_out, ensure_ascii=False, indent=4)
print(f"Tokenized sentences written to {output_file}")
