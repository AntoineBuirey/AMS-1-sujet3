# Built-in modules
import re
import argparse
import os
import json
from typing import Any
import string

# External modules
import nltk
nltk.download('punkt')
nltk.download('punkt_tab') 

from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict
# Local modules
from utils import DebugFunc

from word_type import (TokenType, guess_type_of_token, classify_token_with_context,
                       MUST_BE_CONCATENATED, guess_noun_type, get_verb_data, Mood,
                       identify_subject_for_pronoun)
from verbs_engine import VerbData, mood_map_inv, tense_map_inv, pronoun_map_inv
from standardizer import trim_punctuation, normalize_apostrophes
from count_occurences import count_occurrences

# ===== Constants =====
# Thresholds for promotion/demotion of proper-noun candidates
PROMOTE_MIN_COUNT = 1        # min proper observations to consider a token
PROMOTE_MIN_SCORE = 0.6      # proper / (proper + nonproper_lower)
PROMOTE_MIN_BIGRAM = 1       # min observations for a proper bigram

DEMOTE_MIN_COUNT = 3         # minimum times seen in lowercase to be reliable
DEMOTE_MAX_RATIO = 0.3       # if proper/(proper+nonproper) < 0.3 => demoted

# Tokenization constants
PAGE_BREAK_TOKEN = "__PAGE_BREAK__"
PAGE_NUMBER_REGEX = r"(?:\n� \d+ � \n)|(?:\n\n\n)"



def split_word_with_quote_dash(word : str) -> list[str]:
    """
    Split a word containing a quote or a dash into multiple parts.
    Handle one word at a time. Put the quote/dash with the first part.
    E.g. "l'amour" -> ["l'", "amour"]
    """
    if "'" in word or '-' in word:
        # parts = re.split(r"(')|(-)", word)
        # parts = [part for part in parts if part and part not in ["'", "-"]]
        # return parts
        match = re.match(r"^(.*?['-])(.*)$", word)
        if match:
            return [*match.groups()]
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
    

def split_pages(text: str) -> list[str]:
    """
    Mark page numbers in the text with a special token.
    """
    return re.split(PAGE_NUMBER_REGEX, text)

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

def is_all_caps_sentence(tokens: list[str]) -> bool:
    """Return True if at least ~85% of letter characters are uppercase.

    Useful to detect headings or OCR blocks that are fully uppercased.
    """
    letters = [ch for w in tokens for ch in w if ch.isalpha()]
    if not letters:
        return False
    return sum(ch.isupper() for ch in letters) / len(letters) >= 0.85


def split_sentences(pages: list[str]) -> list[list[str]]:
    """
    Split text into sentences using NLTK's sent_tokenize.
    """
    result: list[list[str]] = []
    for page in pages:
        sentences = sent_tokenize(page, language="french")
        result.append(sentences)
    return result


def load_text(input_file: str) -> list[list[str]]:
    """
    Read input file an return a list of sentences (not lines).
    """
    with open(f"{input_file}", "r", encoding="utf-8") as f:
        text = f.read()

    # some preprocessing operations to simplify text parsing
    text = normalize_apostrophes(text)

    pages = split_pages(text)
    sentences_by_pages = split_sentences(pages)
    
    nb_sentences = sum(len(sents) for sents in sentences_by_pages)
    print("[INFO] Loaded {} sentences from {}".format(nb_sentences, input_file))
    return sentences_by_pages


# --------- PASS 0: sentence preparation ---------
def prepare_sentences(sentences_by_pages: list[list[str]]) -> list[dict[str, int | str | bool | list[str]]]:
    prepared = []
    for page_index, page_sentences in enumerate(sentences_by_pages):
        for i in range(len(page_sentences)):
            maybe_incomplete = False
            original_sentence = page_sentences[i]
            if i == 0 or (i == len(page_sentences) - 1 and original_sentence[-1] not in string.punctuation):
                maybe_incomplete = True
            sentence = original_sentence.strip(" \n\t\r-()")
            sentence = remove_newlines(sentence)
            if sentence == "":
                continue

            tokens = word_tokenize(sentence, language="french")
            tokens = split_words_with_quote_dash(tokens)
            tokens = [t for t in tokens if t.strip() != ""]
            # tokens = [t.strip(string.punctuation) for t in tokens if t.strip(string.punctuation) != ""]
            prepared.append({
                "sentence_index": i,
                "original_sentence": original_sentence,
                "full_sentence": sentence,
                "maybe_incomplete": maybe_incomplete,
                "page_index": page_index,
                "tokens": tokens,
                # Pre-compute ALL-CAPS to tweak proper-noun detection later
                "all_caps": is_all_caps_sentence(tokens)
            })
    return prepared

# --------- PASS A: learn proper nouns from non-ALL-CAPS sentences ---------
def learn_proper_token_stats(prepared: list[dict]) -> tuple[defaultdict, defaultdict, defaultdict]:
    proper_token_count = defaultdict(int)       # normalized token -> count of proper-noun occurrences
    nonproper_lower_count = defaultdict(int)    # normalized token -> count of non-proper occurrences in lowercase
    proper_bigram_count = defaultdict(int)      # (normalized token1, normalized token2) -> count of proper-noun bigram occurrences

    for item in prepared:
        if item["all_caps"]:
            continue
        tokens = item["tokens"]
        flags = [guess_type_of_token(tokens, j) == TokenType.PROPER_NOUN for j in range(len(tokens))]

        # Count tokens
        for j, tok in enumerate(tokens):
            w = trim_punctuation(tok)
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
                t1 = trim_punctuation(tokens[j]); t2 = trim_punctuation(tokens[j+1])
                if t1 and t2:
                    proper_bigram_count[(t1, t2)] += 1
    return proper_token_count, nonproper_lower_count, proper_bigram_count
                
# --------- Promotion/Demotion thresholds ---------
def compute_promotion_demotion(proper_token_count, nonproper_lower_count, proper_bigram_count) -> tuple[set, set, set]:
    promoted_tokens = set()
    for w, c_prop in proper_token_count.items():
        c_non = nonproper_lower_count.get(w, 0)
        score = c_prop / (c_prop + c_non) if (c_prop + c_non) > 0 else 1.0
        if c_prop >= PROMOTE_MIN_COUNT and score >= PROMOTE_MIN_SCORE:
            promoted_tokens.add(w)

    # -------- Auto-demotion --------

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
    return promoted_tokens, promoted_bigrams, auto_demote_tokens



# --------- PASS B: final tagging ---------
def tag_sentence_tokens(prepared: list[dict[str, int | str | bool | list[str]]], promoted_tokens: set, promoted_bigrams: set, auto_demote_tokens: set) -> list[dict]:
    result = []
    for item in prepared:
        tokens = item["tokens"]
        if not isinstance(tokens, list) or not tokens:
            raise ValueError(f"Invalid tokens in item: {item}")
        all_caps = item["all_caps"]
        if not isinstance(all_caps, bool):
            raise ValueError(f"Invalid all_caps in item: {item}")
        words_list_dict : list[dict[str, int|str|Any]] = []
        for j, tok in enumerate(tokens):
            token_type = classify_token_with_context(tokens, j, all_caps, promoted_tokens, promoted_bigrams, auto_demote_tokens)
            if token_type in MUST_BE_CONCATENATED \
            and words_list_dict \
            and words_list_dict[-1]["type"] == token_type.value \
            and (token_type != TokenType.VERB or get_verb_data(tok, words_list_dict, j).mood != Mood.INFINITIF): # do not merge if the second part is an infinitive
                words_list_dict[-1]["word"] += " " + tok # type: ignore
                
                if token_type == TokenType.VERB:
                    # since it's a concatenated verb, we need to update the verb data with the new one
                    try:
                        verb_data = get_verb_data(words_list_dict[-1]["word"], words_list_dict, j)
                    except ValueError as e:
                        # don't merge if the verb not found, mark the second element as ADJECTIVE instead
                        words_list_dict[-1]["word"] = words_list_dict[-1]["word"].rsplit(" ", 1)[0]
                        token_type = TokenType.ADJECTIVE
                        words_list_dict.append({
                            "word": tok,
                            "position": j,
                            "type": token_type.value
                        })
                        print(f"Warning: Could not find verb data for concatenated verb '{words_list_dict[-1]['word']}'. Marking it as ADJECTIVE.")
                        continue
                    words_list_dict[-1]['verb_data'] = {
                        "infinitive": verb_data.infinitive,
                        "mood": mood_map_inv[verb_data.mood],
                        "tense": tense_map_inv[verb_data.tense],
                        "pronoun": pronoun_map_inv[verb_data.pronoun]
                    }                
                
            else:
                token_data : dict[str, int|str|Any] = {
                    "word": tok,
                    "position": j,
                    "type": token_type.value
                }
                if token_type in {TokenType.PROPER_NOUN, TokenType.COMMON_NOUN}:
                    noun_type = guess_noun_type(tokens, words_list_dict, j, token_type)
                    token_data["noun_type"] = noun_type.value
                elif token_type == TokenType.VERB:
                    verb_data = get_verb_data(tok, words_list_dict, j)
                    token_data['verb_data'] = {
                        "infinitive": verb_data.infinitive,
                        "mood": mood_map_inv[verb_data.mood],
                        "tense": tense_map_inv[verb_data.tense],
                        "pronoun": pronoun_map_inv[verb_data.pronoun]
                    }
                words_list_dict.append(token_data)
        if words_list_dict:
            result.append({
                "sentence_index": item["sentence_index"],
                "original_sentence": item["original_sentence"],
                "full_sentence": item["full_sentence"],
                "maybe_incomplete": item["maybe_incomplete"],
                "page_index": item["page_index"],
                "words": words_list_dict
            })
    return result

def filter_person_nouns_only(result: list[dict], keep_only_proper: bool) -> list[dict]:
    for sentence in result:
        sentence["words"] = [word for word in sentence["words"] if (word["type"] in {TokenType.PROPER_NOUN.value, TokenType.COMMON_NOUN.value} and word.get("noun_type") == "person")]
    result = [sentence for sentence in result if sentence["words"]]
    return result

def save_output(result: list[dict], input_file: str):
    output_file = os.path.join("output", os.path.basename(input_file))
    output_file = output_file.replace(".txt", ".parsed.json")

    os.makedirs("output", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f_out:
        json.dump(result, f_out, ensure_ascii=False, indent=4)
    print(f"Tokenized sentences written to {output_file}")


def save_occurences(word_count: dict[str, int], input_file: str):
    output_file = os.path.join("output", os.path.basename(input_file))
    output_file = output_file.replace(".txt", ".wordcount.json")

    os.makedirs("output", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f_out:
        json.dump(word_count, f_out, ensure_ascii=False, indent=4)
    print(f"Word counts written to {output_file}")    


def merge_determiners_nouns(result: list[dict]) -> list[dict]:
    """
    Merge determiners with the following noun into a single token
    if the noun is a common noun representing a person.
    """
    for sentence in result:
        words = sentence["words"]
        merged_words = []
        skip_next = False
        for i in range(len(words)):
            if skip_next:
                skip_next = False
                continue
            word_info = words[i]
            if (word_info["type"] == TokenType.DETERMINER.value and
                i + 1 < len(words) and
                words[i + 1]["type"] == TokenType.COMMON_NOUN.value and
                words[i + 1].get("noun_type") == "person"):
                # Merge determiner with the following noun
                merged_word = {
                    "word": word_info["word"] + " " + words[i + 1]["word"],
                    "position": word_info["position"],
                    "type": TokenType.COMMON_NOUN.value,
                    "noun_type": "person"
                }
                merged_words.append(merged_word)
                skip_next = True
            else:
                merged_words.append(word_info)
        sentence["words"] = merged_words
    return result


def create_link_table(result: list[dict]) -> list[list[str]]:
    """
    Create a link table between persons if they co-occur in the same sentence.
    """
    link_table = []
    for sentence in result:
        persons_in_sentence = [word["word"] for word in sentence["words"]
                               if word["type"] in {TokenType.PROPER_NOUN.value, TokenType.COMMON_NOUN.value}
                               and word.get("noun_type") == "person"]
        for i in range(len(persons_in_sentence)):
            for j in range(i + 1, len(persons_in_sentence)):
                link_table.append([persons_in_sentence[i], persons_in_sentence[j]])
    return link_table


def save_link_table(link_table: list[list[str]], input_file: str):
    output_file = os.path.join("output", os.path.basename(input_file))
    output_file = output_file.replace(".txt", ".linktable.csv")

    os.makedirs("output", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f_out:
        for link in link_table:
            f_out.write(f"{link[0]},{link[1]}\n")
    print(f"Link table written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words.")
    parser.add_argument("input_file", type=str, help="Path to the input text file. Must be in the text_dataset folder.")
    parser.add_argument("--proper", "-p", action="store_true", help="Only keep proper nouns.")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    DebugFunc._debug = args.debug

    input_file = args.input_file
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")

    sentences_by_pages = load_text(input_file)
    prepared = prepare_sentences(sentences_by_pages)
    token_counts = learn_proper_token_stats(prepared)
    promoted_data = compute_promotion_demotion(*token_counts)
    result = tag_sentence_tokens(prepared, *promoted_data)
    
    result = identify_subject_for_pronoun(result)
    
    result = merge_determiners_nouns(result)
    
    if args.proper:
        result = filter_person_nouns_only(result, keep_only_proper=True)
    
    
    word_count = count_occurrences(result)
    
    save_output(result, input_file)
    save_occurences(word_count, input_file)
    link_table = create_link_table(result)
    save_link_table(link_table, input_file)

    


if __name__ == "__main__":
    main()