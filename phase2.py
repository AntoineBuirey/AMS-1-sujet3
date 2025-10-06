# builtin modules
import re
import argparse
import os
import json
import string

# external modules
import nltk
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize

# local modules
from utils import Cache, DebugFunc




def split_word_with_quote_dash(word : str) -> list[str]:
    """
    Split a word containing a quote or a dash into multiple parts.
    Handle one word at a time.
    E.g. "l'amour" -> ["l'", "amour"]
    """
    if "'" in word or '-' in word:
        # parts = word.split("'")
        parts = re.split(r"(')|(-)", word)
        parts = [part for part in parts if part and part not in ["'", "-"]]
        # print(f"Splitting word with quote: {word} -> {parts}")
        return parts
    return [word]

def split_words_with_quote_dash(words : list[str]) -> list[str]:
    """
    Split words containing quotes or dashes into multiple parts.
    Handle a complete sentence at once.
    E.g. ["l'amour", "est", "beau"] -> ["l'", "amour", "est", "beau"]
    """
    result = []
    for word in words:
        result.extend(split_word_with_quote_dash(word))
    return result
    

def is_determinant(word : str) -> bool:
    """
    Check if a word is a determinant (article, demonstrative, possessive).
    """
    determinants = ["le", "la", "les", "un", "une", "des", "du", "l'"]
    suffixes = ["-le", "-la", "-les", "-un", "-une", "-des", "-du", "-l'", "-il", "-elle", "-ils", "-elles",
                "-vous", "-nous", "-mon", "-ma", "-mes", "-ton", "-ta", "-tes", "-son", "-sa", "-ses",
                "-notre", "-nos", "-votre", "-vos", "-ce", "-cette", "-ces", "-y"]
    return word.lower() in determinants or any(word.lower().endswith(suffix) for suffix in suffixes)

@DebugFunc
def is_pronoun(word : str) -> bool:
    """
    Check if a word is a pronoun (personal, reflexive, possessive, demonstrative).
    """
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
    """
    Check if a word is an adverb.
    """
    adverbs = [
    "aujourd'hui", "d'abord", "difficilement", "doute",
        "lentement", "là-bas", "part", "peut-être",
        "vite", "oh", "aussi", "naturellement", "jamais",]
    return word.lower() in adverbs

def mark_page_numbers(text: str) -> str:
    """
    Mark page numbers in the text with a special token.
    """
    return re.sub(r"\n� \d+ � \n", '__PAGE_BREAK__', text) # using __PAGE_BREAK__ as a placeholder for page breaks

def remove_newlines(text: str) -> str:
    """
    Remove newlines from the text, replacing them with spaces where appropriate.
    """
    # \n must be replaced by a space only if it is not preceded by a period or followed by a lowercase letter
    # else, it must be just removed
    text = re.sub(r"(?<!\.)\n(?![a-zàâäéèêëïîôöùûüç])", " ", text)
    text = re.sub(r"(?<=\.)\n", "", text)
    text = re.sub(r"(?<!\.)\n", " ", text)
    # Finally, replace multiple spaces by a single space
    text = re.sub(r" +", " ", text)
    return text

@DebugFunc
def is_proper_noun(sentence : list[str], index : int) -> bool:
    """
    Check if a word in a sentence is a proper noun.
    A proper noun is defined as a word that starts with a capital letter,
    is not the first word of the sentence (unless it is the only word),
    is not a functional word (determiner, pronoun, adverb, etc.),
    and contains at least one letter.
    """
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
    """
    Get a list of functional words (determiners, pronouns, adverbs, etc.) from predefined files.
    """
    words : list[str] = []
    files = ["fonctionnels_fr.txt", "verbes.txt"]
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            words += f.read().splitlines()
    return [word.lower() for word in words if not word.startswith("#") and word.strip() != ""]



# Main script

parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
parser.add_argument("--proper", "-p", action="store_true", help="Only keep proper nouns.")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode.")
args = parser.parse_args()

DebugFunc._debug = args.debug

with open(f"text_dataset/{args.input_file}", "r", encoding="utf-8") as f:
    text = f.read()

text = mark_page_numbers(text)
    
# same file name, but in the output folder
output_file = os.path.join("output", os.path.basename(args.input_file))
output_file = output_file.replace(".txt", ".parsed.json")

# Split text into sentences using regex to handle specific cases
# This regex splits at ., !, ? if preceded by at least two letters or a closing parenthesis or a quote
# It also splits at ... followed by space, or at quotes, or at - digit -
sentences = re.split(r'(?<=[\w )\"]{2}[.!?])|\.\.\.\ +|\"|- \d -', text)


# Since we got 1 page over 2, some sentences are have a missing part due to page breaks.
# The goal here is to detect these cases and split the sentence into two sentences over the page break.
# Later, the __PAGE_BREAK__ marker will be removed, and a "maybe_incomplete" flag will be set to True for these sentences.
# Theses sentences will have a higher error probability when counting proper nouns
for i in range(len(sentences)):
    if "__PAGE_BREAK__" in sentences[i]:  # page break
        sentences[i], s2 = sentences[i].split("__PAGE_BREAK__", 1)
        sentences[i] += "__PAGE_BREAK__"
        s2 = "__PAGE_BREAK__" + s2
        sentences.insert(i + 1, s2)
        i += 1

result = []
for i in range(len(sentences)):
    maybe_incomplete = False
    original_sentence = sentences[i]
    if "__PAGE_BREAK__" in original_sentence:  # set the flag and remove the marker for incomplete sentences
        maybe_incomplete = True
        original_sentence = original_sentence.replace("__PAGE_BREAK__", "")
    sentence = original_sentence.strip(" \n\t\r-()")
    sentence = remove_newlines(sentence)
    
    # Skip empty sentences
    if sentence == "":
        continue

    words_list = word_tokenize(sentence, language="french")
    words_list = split_words_with_quote_dash(words_list)
    words_list_dict = []
    for j in range(len(words_list)):
        words_list[j] = words_list[j].strip(string.punctuation)
        if words_list[j] == "":
            continue
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
            "original_sentence": original_sentence,
            "full_sentence": sentence,
            "maybe_incomplete": maybe_incomplete,
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
