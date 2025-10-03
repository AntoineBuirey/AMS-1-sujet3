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
    

def is_determinant(word : str) -> bool:
    determinants = ["le", "la", "les", "un", "une", "des", "du", "l'"]
    return word.lower() in determinants

@DebugFunc
def is_pronoun(word : str) -> bool:
    pronouns = ["je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
                "me", "te", "se", "moi", "toi", "lui", "eux",
                "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
                "notre", "nos", "votre", "vos",
                "ce", "cette", "ces",
                "on"]
    return word.lower() in pronouns
@DebugFunc
def is_adverbe(word : str) -> bool:
    adverbs = [
    "très", "trop", "assez", "beaucoup", "peu", "tellement", "autant",

    "bien", "mal", "vite", "lentement", "facilement", "difficilement", "ainsi",

    "toujours", "souvent", "parfois", "jamais", "encore", "déjà", "enfin",
    "maintenant", "bientôt", "longtemps", "aujourd’hui", "demain", "hier",

    "ici", "là", "là-bas", "ailleurs", "dedans", "dehors", "partout",
    "nulle part", "devant", "derrière", "dessus", "dessous",

    "oui", "non", "si", "peut-être", "sûrement", "probablement",
    "évidemment", "certainement", "sans doute","sur",

    "alors", "donc", "puis", "ensuite", "d’abord"]
    return word.lower() in adverbs

@DebugFunc
def is_proper_noun(sentence : list[str], index : int) -> bool:
    word = sentence[index]
    if index == 0:
        if any(char in word for char in string.ascii_letters):  # first word of the sentence and contains at least one letter
            # return not is_determinant(word) and not is_pronoun(word)
            return word.lower() not in get_fonctional_words()
    else:
        if word[0].isupper():            # not the first word of the sentence and starts with a capital letter
            return True
    return False


@Cache
def get_fonctional_words() -> list[str]:
    with open("fonctionnels_fr.txt", "r", encoding="utf-8") as f:
        words = f.read().splitlines()
    return [word.lower() for word in words if not word.startswith("#") and word.strip() != ""]



parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
parser.add_argument("--proper", "-p", action="store_true", help="Only keep proper nouns.")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode.")
args = parser.parse_args()

DebugFunc._debug = args.debug

with open(f"text_dataset/{args.input_file}", "r", encoding="utf-8") as f:
    text = f.read()
    
# same file name, but in the output folder
output_file = os.path.join("output", os.path.basename(args.input_file))
output_file = output_file.replace(".txt", ".parsed.json")

# Split text into sentences using regex to handle specific cases
# This regex splits at ., !, ? if preceded by at least two letters or a closing parenthesis or a quote
# It also splits at ... followed by space, or at quotes, or at - digit -
sentences = re.split(r'(?<=[\w )\"]{2}[.!?])|\.\.\. +|\"|- \d -', text)



result = []
for i in range(len(sentences)):
    sentence = sentences[i].strip(" \n\t\r-")
    if sentence == "":
        continue

    words_list = word_tokenize(sentence, language="french")
    words_list_dict = []
    for j in range(len(words_list)):
        word = words_list[j]
        is_proper = is_proper_noun(words_list, j)
        if args.proper and not is_proper:
            continue
        
        if is_proper and words_list_dict and words_list_dict[-1]["is_proper_noun"]:
            words_list_dict[-1]["word"] += " " + word
            continue
        else:
            words_list_dict.append({
                "word": word,
                "is_proper_noun": is_proper
            })
    if words_list_dict:
        result.append(words_list_dict)

os.makedirs("output", exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f_out:
    json.dump(result, f_out, ensure_ascii=False, indent=4)
print(f"Tokenized sentences written to {output_file}")
