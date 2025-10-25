# Built-in modules
import re
import argparse
import os
import json
import string

# External modules
import nltk
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict
# Local modules
from utils import Cache, DebugFunc




# ===== Constants =====
# Thresholds for promotion/demotion of proper-noun candidates
PROMOTE_MIN_COUNT = 1        # min proper observations to consider a token
PROMOTE_MIN_SCORE = 0.6      # proper / (proper + nonproper_lower)
PROMOTE_MIN_BIGRAM = 1       # min observations for a proper bigram

DEMOTE_MIN_COUNT = 3         # minimum times seen in lowercase to be reliable
DEMOTE_MAX_RATIO = 0.3       # if proper/(proper+nonproper) < 0.3 => demoted

# Tokenization constants
PAGE_BREAK_TOKEN = "__PAGE_BREAK__"
PAGE_NUMBER_REGEX = r"\n� \d+ � \n"

# Language resource lists
DETERMINERS = ["le", "la", "les", "un", "une", "des", "du", "l'"]
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
]

def split_word_with_quote_dash(word : str) -> list[str]:
    """
    Split a word containing a quote or a dash into multiple parts.
    Handle one word at a time.
    E.g. "l'amour" -> ["l'", "amour"]
    """
    if "'" in word or '-' in word:
        parts = re.split(r"(')|(-)", word)
        parts = [part for part in parts if part and part not in ["'", "-"]]
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
    return word.lower() in DETERMINERS or any(word.lower().endswith(suffix) for suffix in DETERMINER_SUFFIXES)

@DebugFunc
def is_pronoun(word : str) -> bool:
    """
    Check if a word is a pronoun (personal, reflexive, possessive, demonstrative).
    """
    w = word.lower()
    return w in PRONOUNS or any(word.startswith(prefix) for prefix in PRONOUN_PREFIXES)

@Cache
def is_adverbe(word : str) -> bool:
    """
    Check if a word is an adverb.
    """
    return word.lower() in ADVERBS

def mark_page_numbers(text: str) -> str:
    """
    Mark page numbers in the text with a special token.
    """
    # Use PAGE_BREAK_TOKEN as a placeholder for page breaks (pattern: \n� N � \n)
    return re.sub(PAGE_NUMBER_REGEX, PAGE_BREAK_TOKEN, text)

def remove_newlines(text: str) -> str:
    """
    Remove newlines from the text, replacing them with spaces where appropriate.
    """
    # Replace a newline with a space only if it is not preceded by a period and not followed by a lowercase letter;
    # otherwise, remove it. Finally, collapse multiple spaces.
    text = re.sub(r"(?<!\.)\n(?![a-zàâäéèêëïîôöùûüç])", " ", text)
    text = re.sub(r"(?<=\.)\n", "", text)
    text = re.sub(r"(?<!\.)\n", " ", text)
    # Finally, replace multiple spaces by a single space
    text = re.sub(r" +", " ", text)
    return text
def normalize_token(w: str) -> str:
    """Trim surrounding punctuation and lowercase the token."""
    return w.strip(string.punctuation).lower()

def is_all_caps_sentence(tokens: list[str]) -> bool:
    """Return True if at least ~85% of letter characters are uppercase.

    Useful to detect headings or OCR blocks that are fully uppercased.
    """
    letters = [ch for w in tokens for ch in w if ch.isalpha()]
    if not letters:
        return False
    return sum(ch.isupper() for ch in letters) / len(letters) >= 0.85

def is_acronym(word: str) -> bool:
    """Heuristic: token with 2+ letters and all letters uppercase."""
    alpha = ''.join(ch for ch in word if ch.isalpha())
    return len(alpha) >= 2 and alpha.isupper()


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
def is_proper_noun_ctx(sentence_tokens: list[str], index: int, all_caps: bool,
                       known_proper_tokens=None, known_proper_bigrams=None) -> bool:
    """Context-aware proper-noun detector.

    - Applies functional-word guards and optional auto-demotion list.
    - If sentence is not ALL-CAPS, delegates to basic `is_proper_noun`.
    - In ALL-CAPS sentences, promotes acronyms, known tokens, and known bigrams.
    """
    word = sentence_tokens[index]
    wnorm = normalize_token(word)
    if not wnorm:
        return False

    # Guards: functional words, pronouns, adverbs, determiners, or auto-demoted tokens
    try:
        auto_demoted = (wnorm in auto_demote_tokens)
    except NameError:
        auto_demoted = False  # default to no demotion if the set is not built yet
    if (wnorm in get_fonctional_words()
        or is_pronoun(word)
        or is_adverbe(word)
        or is_determinant(word)
        or auto_demoted):
        return False

    if not all_caps:
        return is_proper_noun(sentence_tokens, index)

    # ===== Minimal logic for ALL-CAPS sentences =====
    if is_acronym(word):
        return True

    try:
        if wnorm in promoted_tokens:
            return True
        prev = normalize_token(sentence_tokens[index-1]) if index-1 >= 0 else ""
        nxt  = normalize_token(sentence_tokens[index+1]) if index+1 < len(sentence_tokens) else ""
        if (wnorm, nxt) in promoted_bigrams or (prev, wnorm) in promoted_bigrams:
            return True
    except NameError:
        # Promotion sets not yet available; fall through.
        pass

    return False





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



# Main script

parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
parser.add_argument("--proper", "-p", action="store_true", help="Only keep proper nouns.")
parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode.")
args = parser.parse_args()

DebugFunc._debug = args.debug

input_file = args.input_file
if input_file.startswith("text_dataset/"):
    input_file = input_file[13:]
if not os.path.isfile(f"text_dataset/{input_file}"):
    print(f"[ERROR] Input file text_dataset/{input_file} does not exist.")
    exit(1)

with open(f"text_dataset/{input_file}", "r", encoding="utf-8") as f:
    text = f.read()

text = mark_page_numbers(text)
    
# same file name, but in the output folder
output_file = os.path.join("output", os.path.basename(input_file))
output_file = output_file.replace(".txt", ".parsed.json")

# Split text into sentences with a regex tuned for noisy text (e.g., OCR):
# - split at ., !, ? if preceded by at least two word/paren/quote chars
# - split at ellipsis + space ("... "), at quotes, or at patterns like "- digit -"
sentences = re.split(r'(?<=[\w )\"]{2}[.!?])|\.\.\.\ +|\"|- \d -', text)


# When every other page is present, sentences may be cut by page breaks.
# Detect and split around __PAGE_BREAK__ so we can flag possibly incomplete sentences.
for i in range(len(sentences)):
    if PAGE_BREAK_TOKEN in sentences[i]:  # page break
        sentences[i], s2 = sentences[i].split(PAGE_BREAK_TOKEN, 1)
        sentences[i] += PAGE_BREAK_TOKEN
        s2 = PAGE_BREAK_TOKEN + s2
        sentences.insert(i + 1, s2)
        i += 1

# --------- PASS 0: sentence preparation ---------
prepared = []
for i in range(len(sentences)):
    maybe_incomplete = False
    original_sentence = sentences[i]
    if PAGE_BREAK_TOKEN in original_sentence:
        maybe_incomplete = True
        original_sentence = original_sentence.replace(PAGE_BREAK_TOKEN, "")
    sentence = original_sentence.strip(" \n\t\r-()")
    sentence = remove_newlines(sentence)
    if sentence == "":
        continue

    tokens = word_tokenize(sentence, language="french")
    tokens = split_words_with_quote_dash(tokens)
    tokens = [t.strip(string.punctuation) for t in tokens if t.strip(string.punctuation) != ""]
    prepared.append({
        "sentence_index": i,
        "original_sentence": original_sentence,
        "full_sentence": sentence,
        "maybe_incomplete": maybe_incomplete,
        "tokens": tokens,
        # Pre-compute ALL-CAPS to tweak proper-noun detection later
        "all_caps": is_all_caps_sentence(tokens)
    })

# --------- PASS A: learn proper nouns from non-ALL-CAPS sentences ---------
proper_token_count = defaultdict(int)
nonproper_lower_count = defaultdict(int)
proper_bigram_count = defaultdict(int)

for item in prepared:
    if item["all_caps"]:
        continue
    tokens = item["tokens"]
    flags = [is_proper_noun(tokens, j) for j in range(len(tokens))]

    # Count tokens
    for j, tok in enumerate(tokens):
        w = normalize_token(tok)
        if not w:
            continue
        if flags[j]:
            proper_token_count[w] += 1
        else:
            # Only count "non-proper" if the token is observed in lowercase
            if tok and tok[0].islower():
                nonproper_lower_count[w] += 1

    # Count consecutive bigrams tagged as proper
    for j in range(len(tokens)-1):
        if flags[j] and flags[j+1]:
            t1 = normalize_token(tokens[j]); t2 = normalize_token(tokens[j+1])
            if t1 and t2:
                proper_bigram_count[(t1, t2)] += 1
                
# --------- Promotion/Demotion thresholds ---------
PROMOTE_MIN_COUNT = 1        # min proper observations to consider a token
PROMOTE_MIN_SCORE = 0.6      # proper / (proper + nonproper_lower)
PROMOTE_MIN_BIGRAM = 1       # min observations for a proper bigram

promoted_tokens = set()
for w, c_prop in proper_token_count.items():
    c_non = nonproper_lower_count.get(w, 0)
    score = c_prop / (c_prop + c_non) if (c_prop + c_non) > 0 else 1.0
    if c_prop >= PROMOTE_MIN_COUNT and score >= PROMOTE_MIN_SCORE:
        promoted_tokens.add(w)

# -------- Auto-demotion --------
DEMOTE_MIN_COUNT = 3        # minimum times seen in lowercase to be reliable
DEMOTE_MAX_RATIO = 0.3      # if proper/(proper+nonproper) < 0.3 => demoted

auto_demote_tokens = set()
for w, c_non in nonproper_lower_count.items():
    c_prop = proper_token_count.get(w, 0)
    total = c_prop + c_non
    if total >= DEMOTE_MIN_COUNT:
        ratio = c_prop / total
        if ratio < DEMOTE_MAX_RATIO:
            auto_demote_tokens.add(w)

print(f"[INFO] Auto-demoted: {len(auto_demote_tokens)} tokens, e.g.: {list(auto_demote_tokens)[:10]}")

promoted_bigrams = {bg for bg, c in proper_bigram_count.items() if c >= PROMOTE_MIN_BIGRAM}



# --------- PASS B: final tagging ---------
result = []
for item in prepared:
    tokens = item["tokens"]
    all_caps = item["all_caps"]
    words_list_dict = []
    for j, tok in enumerate(tokens):
        is_prop = is_proper_noun_ctx(tokens, j, all_caps)
        if is_prop and words_list_dict and words_list_dict[-1]["is_proper_noun"]:
            words_list_dict[-1]["word"] += " " + tok
        else:
            words_list_dict.append({
                "word": tok,
                "is_proper_noun": is_prop,
                "position": j
            })
    if words_list_dict:
        result.append({
            "sentence_index": item["sentence_index"],
            "original_sentence": item["original_sentence"],
            "full_sentence": item["full_sentence"],
            "maybe_incomplete": item["maybe_incomplete"],
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
