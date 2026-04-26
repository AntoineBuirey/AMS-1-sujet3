# Built-in modules
import re
import argparse
import os
from typing import Any
import string


# External modules
import nltk
def init_nltk():
    Logger.info("Initializing NLTK and downloading required resources...")
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    Logger.info("NLTK initialization complete.")

from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict
import pandas as pd
from gamuLogger import Logger, config_argparse, config_logger
# Local modules

from .word_type import (TokenType, guess_type_of_token, classify_token_with_context,
                       MUST_BE_CONCATENATED, guess_noun_type, get_verb_data, Mood,
                       identify_subject_for_pronoun)
from .verbs_engine import mood_map_inv, tense_map_inv, pronoun_map_inv
from .standardizer import trim_punctuation, normalize_apostrophes, lowercase
from .count_occurences import count_occurrences
from .alias_resolution import resolve_aliases
from .create_graph import create_graph, save_img_graph, to_graphml
from .lien_personnage import build_links_file
from .utils import save_structure_data, get_output_dir, append_to_file, save_graphml_file
from .spacy_helper import get_nlp
from .relation_polarity import reset_book_scores, save_pairs


# logger setup
Logger.set_module("main")


# ===== Constants =====
PROMOTE_MIN_COUNT = 2
PROMOTE_MIN_SCORE = 0.7
PROMOTE_MIN_BIGRAM = 1

DEMOTE_MIN_COUNT = 1
DEMOTE_MAX_RATIO = 0.15

PAGE_BREAK_TOKEN = "__PAGE_BREAK__"
PAGE_NUMBER_REGEX = r"(?:\n\ufffd \d+ \ufffd \n)|(?:\n\n\n)"


def split_word_with_quote_dash(word: str) -> list[str]:
    if "'" in word or '-' in word:
        match = re.match(r"^(.*?['-])(.*)$", word)
        if match:
            return [*match.groups()]
    return [word]

def split_words_with_quote_dash(words: list[str]) -> list[str]:
    result = []
    for word in words:
        result.extend(split_word_with_quote_dash(word))
    return result

def split_pages(text: str) -> list[str]:
    return re.split(PAGE_NUMBER_REGEX, text)

def remove_newlines(text: str) -> str:
    text = re.sub(r"(?<!\.)\n(?![a-zàâäéèêëïîôöùûüç])", " ", text)
    text = re.sub(r"(?<=\.)\n", "", text)
    text = re.sub(r"(?<!\.)\n", " ", text)
    text = re.sub(r" +", " ", text)
    return text

def is_all_caps_sentence(tokens: list[str]) -> bool:
    letters = [ch for w in tokens for ch in w if ch.isalpha()]
    if not letters:
        return False
    return sum(ch.isupper() for ch in letters) / len(letters) >= 0.85

def split_sentences(pages: list[str]) -> list[list[str]]:
    result: list[list[str]] = []
    for page in pages:
        sentences = sent_tokenize(page, language="french")
        result.append(sentences)
    return result

def load_text(input_file: str) -> list[list[str]]:
    with open(f"{input_file}", "r", encoding="utf-8") as f:
        text = f.read()
    text = normalize_apostrophes(text)
    pages = split_pages(text)
    sentences_by_pages = split_sentences(pages)
    nb_sentences = sum(len(sents) for sents in sentences_by_pages)
    Logger.info(f"Loaded {nb_sentences} sentences from {input_file}")
    return sentences_by_pages

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
            prepared.append({
                "sentence_index": i,
                "original_sentence": original_sentence,
                "full_sentence": sentence,
                "maybe_incomplete": maybe_incomplete,
                "page_index": page_index,
                "tokens": tokens,
                "all_caps": is_all_caps_sentence(tokens)
            })
    return prepared

def learn_proper_token_stats(prepared: list[dict]) -> tuple[defaultdict, defaultdict, defaultdict]:
    proper_token_count = defaultdict(int)
    nonproper_lower_count = defaultdict(int)
    proper_bigram_count = defaultdict(int)
    for item in prepared:
        if item["all_caps"]:
            continue
        tokens = item["tokens"]
        flags = [guess_type_of_token(tokens, j) == TokenType.PROPER_NOUN for j in range(len(tokens))]
        for j, tok in enumerate(tokens):
            w = trim_punctuation(tok)
            if not w:
                continue
            if flags[j]:
                proper_token_count[w] += 1
            else:
                if tok and tok[0].islower():
                    nonproper_lower_count[w] += 1
        for j in range(len(tokens)-1):
            if flags[j] and flags[j+1]:
                t1 = trim_punctuation(tokens[j]); t2 = trim_punctuation(tokens[j+1])
                if t1 and t2:
                    proper_bigram_count[(t1, t2)] += 1
    return proper_token_count, nonproper_lower_count, proper_bigram_count

def compute_promotion_demotion(proper_token_count, nonproper_lower_count, proper_bigram_count) -> tuple[set, set, set]:
    promoted_tokens = set()
    for w, c_prop in proper_token_count.items():
        c_non = nonproper_lower_count.get(w, 0)
        score = c_prop / (c_prop + c_non) if (c_prop + c_non) > 0 else 1.0
        if c_prop >= PROMOTE_MIN_COUNT and score >= PROMOTE_MIN_SCORE:
            promoted_tokens.add(w)
    auto_demote_tokens = set()
    for w, c_non in nonproper_lower_count.items():
        c_prop = proper_token_count.get(w, 0)
        total = c_prop + c_non
        if total >= DEMOTE_MIN_COUNT:
            ratio = c_prop / total
            if ratio < DEMOTE_MAX_RATIO:
                auto_demote_tokens.add(w)
    Logger.info(f"Auto-demoted: {len(auto_demote_tokens)} tokens\nfirst 10: {list(auto_demote_tokens)[:10]}")
    promoted_bigrams = {bg for bg, c in proper_bigram_count.items() if c >= PROMOTE_MIN_BIGRAM}
    return promoted_tokens, promoted_bigrams, auto_demote_tokens

def tag_sentence_tokens(prepared: list[dict[str, int | str | bool | list[str]]], promoted_tokens: set, promoted_bigrams: set, auto_demote_tokens: set, store_unknow_verb: str | None = None) -> list[dict]:
    result = []
    potential_persons = defaultdict(int)
    for item in prepared:
        tokens = item["tokens"]
        if not isinstance(tokens, list) or not tokens:
            raise ValueError(f"Invalid tokens in item: {item}")
        all_caps = item["all_caps"]
        if not isinstance(all_caps, bool):
            raise ValueError(f"Invalid all_caps in item: {item}")
        words_list_dict: list[dict[str, int | str | Any]] = []
        for j, tok in enumerate(tokens):
            token_type = classify_token_with_context(tokens, j, all_caps, promoted_tokens, promoted_bigrams, auto_demote_tokens)
            if token_type in MUST_BE_CONCATENATED \
            and words_list_dict \
            and words_list_dict[-1]["type"] == token_type.value \
            and (token_type != TokenType.VERB or get_verb_data(tok, words_list_dict, j).mood != Mood.INFINITIF):
                words_list_dict[-1]["word"] += " " + tok
                if token_type == TokenType.VERB:
                    word = words_list_dict[-1]["word"].strip("-")
                    try:
                        verb_data = get_verb_data(words_list_dict[-1]["word"], words_list_dict, j)
                    except ValueError as e:
                        words_list_dict[-1]["word"] = words_list_dict[-1]["word"].rsplit(" ", 1)[0]
                        words_list_dict.append({"word": tok, "position": j, "type": TokenType.ADJECTIVE.value})
                        prev_token = words_list_dict[-2]
                        Logger.debug(f"{e}\ndefaulting to:\n\t{prev_token['word']:10} {prev_token['type']}\n\t{tok:10} adjective")
                        if store_unknow_verb:
                            append_to_file(store_unknow_verb, words_list_dict[-1]['word'])
                        continue
                    words_list_dict[-1]['verb_data'] = {
                        "infinitive": verb_data.infinitive,
                        "mood": mood_map_inv[verb_data.mood],
                        "tense": tense_map_inv[verb_data.tense],
                        "pronoun": pronoun_map_inv[verb_data.pronoun]
                    }
            else:
                token_data: dict[str, int | str | Any] = {"word": tok, "position": j, "type": token_type.value}
                if token_type in {TokenType.PROPER_NOUN, TokenType.COMMON_NOUN}:
                    maybe_incomplete_sentence : bool = item["maybe_incomplete"] #type: ignore
                    try:
                        noun_type, reason = guess_noun_type(tokens, words_list_dict, j, token_type, maybe_incomplete_sentence)
                    except Exception as e:
                        Logger.error(f"Error guessing noun type for token '{tok}' in sentence '{item['full_sentence']}' (index {j}): {e}")
                        Logger.error(words_list_dict)
                        raise
                    token_data["noun_type"] = noun_type.value
                    token_data["noun_type_reason"] = reason
                    if noun_type.value == "person":
                        potential_persons[tok] += 1
                    elif token_type == TokenType.PROPER_NOUN:
                        Logger.debug(f"Proper noun NOT classified as person: '{tok}' (reason: {reason})")
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
    Logger.info(f"Found {len(potential_persons)} potential person entities")
    sorted_persons = sorted(potential_persons.items(), key=lambda x: x[1], reverse=True)
    Logger.debug(f"Top 20 potential persons:\n" + "\n".join([f"  {name}: {count}" for name, count in sorted_persons[:20]]))
    return result

def merge_determiners_nouns(result: list[dict]) -> list[dict]:
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
                merged_word = {
                    "word": word_info["word"] + " " + words[i + 1]["word"],
                    "position": word_info["position"],
                    "type": TokenType.COMMON_NOUN.value,
                    "noun_type": "person",
                    "noun_type_reason": f"merged determiner with person common noun (from '{words[i + 1]['noun_type_reason']}')"
                }
                merged_words.append(merged_word)
                skip_next = True
            else:
                merged_words.append(word_info)
        sentence["words"] = merged_words
    return result

def get_book_chapter(input_file: str) -> tuple[str, int]:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")
    base_name = os.path.basename(input_file)
    match = re.match(r"([a-zA-Z]+)[._-]chapter[_-](\d+)\.txt$", base_name)
    if not match:
        raise ValueError(f"Input file name {base_name} does not match expected pattern '[code].chapter_[number].txt'")
    return match.group(1), int(match.group(2))


# =============================================================================
# Blacklist
# =============================================================================
PERSON_BLACKLIST: frozenset[str] = frozenset({
    # Lieux PAF + LCA
    "trantor", "terminus", "helicon", "hélicon", "anacreon", "mycogene", "mycogène",
    "kalgan", "korell", "askone", "smyrno", "sayshell", "gaia",
    "spacetown", "aurora", "solaria", "comporellon",
    "billibotton", "dahl", "streeling", "sacratorium", "microferme",
    # Ethnonymes
    "spaciens", "spacien", "spacienne", "spaciennes",
    "terriens", "terrien", "terrienne",
    "galactiques", "galactique",
    "trantorien", "trantoriens", "trantorienne",
    "mycogeniens", "mycogéniens", "mycogénien", "mycogénienne", "mycogéniennes",
    "kanite",
    # Entités non-personnages Fondation
    "encyclopaedia galactica", "encyclopaedia", "galactica",
    "plan seldon", "plan", "empire galactique", "empire",
    "premiere fondation", "seconde fondation", "fondation",
    "goutte-de-pluie quarante", "goutte-de-pluie", "goutte de pluie",
    # Verbes / syntagmes mal classifiés
    "exact", "souligner", "précéda", "le précéda",
    "cette croyance", "affirmer", "sembler",
    "etant", "étant", "voila", "voilà",
    "mis", "des principes", "votre rythme",
    "neutralisez", "concevoir",
    # Verbes à l'impératif
    "ecoute", "ecoutez", "ecoutez-", "reponds", "commandez",
    "etait-", "tais-toi", "fermez-", "réponds", "reponds-",
    # Titres génériques seuls
    "monsieur", "madame", "mademoiselle",
    "frere", "frère", "professeur",
    "sergent", "maire",
    "maitresse", "maîtresse",
    "soeur", "sœur", "soeurs", "sœurs",
    # Objets / concepts
    "livre", "robot",
    # Artefacts OCR
    "― sire ‖", "sire ‖",
    "maitre-", "maître-", "f- frere", "f- frère",
    "bande-", "ba-lee", "da- nee", "e.g",
    "seldon acquiesça", "sauvetage",
    "mycélium soixante-douze", "mycélium", "mycélium soixante-",
    "t- e-r-r-a", "terra",
    # Lieux US
    "new york", "new york city", "new jersey", "chicago", "washington",
    # Organisations
    "police", "la police", "garde",
    "medievalistes", "médiévalistes", "subdivisions ia",
    # Syntagmes mal classifiés
    "ciel", "votre desir", "votre désir", "affaire sarton",
    "cette affaire", "cette affaire sarton",
    "sa culture et", "les predictions et", "les prédictions et",
    "toute apparence", "de maison", "la tradition", "le rite",
    "tite dame",
    # Dynasties / organisations
    "dynastie entun",
    # Autres faux positifs
    "historienne", "renégat", "renegat",
})


def _is_blacklisted(name: str) -> bool:
    if "\n" in name:
        return True
    if len(name) > 50:
        return True
    if not any(c.isalpha() for c in name):
        return True
    return name.lower().strip() in PERSON_BLACKLIST


def filter_word_count(word_count: dict[str, int]) -> dict[str, int]:
    filtered = {n: c for n, c in word_count.items() if not _is_blacklisted(n)}
    removed = set(word_count) - set(filtered)
    if removed:
        Logger.info(f"Blacklist: {len(removed)} entrées supprimées → {sorted(removed)}")
    return filtered


def clean_ocr_text(text: str) -> str:
    text = re.sub(r'\n\n+', '\x00', text)
    text = re.sub(
        r'([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç]*)\n([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ])',
        r'\1 \2', text
    )
    text = text.replace('\x00', '\n\n')
    return text


def extract_persons_spacy(text: str) -> dict[str, int]:
    nlp = get_nlp()
    text = clean_ocr_text(text)
    MAX_CHUNK = 100_000
    spacy_counts: dict[str, int] = {}
    STRIP_CHARS = ".,;:!?\"'()[]{}«»\u201c\u201d\u2018\u2019\u2014-\u2013\u2026"
    for start in range(0, len(text), MAX_CHUNK):
        doc = nlp(text[start:start + MAX_CHUNK])
        for ent in doc.ents:
            if ent.label_ != "PER":
                continue
            name = ent.text.strip().strip(STRIP_CHARS).strip()
            if not name or len(name) <= 1 or name.isdigit():
                continue
            if _is_blacklisted(name):
                continue
            spacy_counts[name] = spacy_counts.get(name, 0) + 1
    Logger.info(f"spaCy NER: {len(spacy_counts)} entités PER après filtre")
    return spacy_counts


def merge_word_counts(primary: dict[str, int],
                      secondary: dict[str, int],
                      min_spacy_count: int = 2) -> dict[str, int]:
    merged = dict(primary)
    for name, count in secondary.items():
        if name in merged:
            merged[name] += count
        elif count >= min_spacy_count:
            merged[name] = count
    return dict(sorted(merged.items(), key=lambda x: x[1], reverse=True))


def build_characters_graph(
    input_file: str,
    save_intermediate: bool = False,
    save_graph_image: bool = False,
    show_vertices_labels: bool = False,
    save_unknow_verb: str | None = None,
    save_graphml: bool = False,
    compute_polarity: bool = True,   # ← réseau signé activé par défaut
) -> str:
    book_code, chapter_number = get_book_chapter(input_file)

    sentences_by_pages = load_text(input_file)
    prepared = prepare_sentences(sentences_by_pages)
    token_counts = learn_proper_token_stats(prepared)
    promoted_data = compute_promotion_demotion(*token_counts)
    result = tag_sentence_tokens(prepared, *promoted_data, save_unknow_verb)

    result = identify_subject_for_pronoun(result)
    result = merge_determiners_nouns(result)

    # NER primaire
    word_count = count_occurrences(result)
    Logger.info(f"NER custom: {len(word_count)} personnages")
    word_count = filter_word_count(word_count)

    # NER secondaire (spaCy)
    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()
    spacy_wc = extract_persons_spacy(raw_text)
    word_count = merge_word_counts(word_count, spacy_wc, min_spacy_count=2)
    Logger.info(f"NER fusionné: {len(word_count)} personnages")

    # Résolution d'alias
    aliases = resolve_aliases(list(word_count.keys()), word_count=word_count)
    canonical_names = [group[0] for group in aliases]

    # Liens avec polarité optionnelle
    link_table = build_links_file(
        input_file,
        canonical_names,
        aggregated=True,
        window=25,
        min_count=1,
        external_alias_map={name: name for name in canonical_names},
        compute_polarity=compute_polarity,
    )

    output_dir = get_output_dir(book_code, chapter_number)

    if save_intermediate:
        save_structure_data(aliases, output_dir, "aliases")
        save_structure_data(link_table, output_dir, "link_table")
        save_structure_data(result, output_dir, "parsed_sentences")
        save_structure_data(word_count, output_dir, "word_count")

    graph = create_graph(aliases, link_table)

    if save_graph_image:
        save_img_graph(
            graph,
            os.path.join(output_dir, "graph.png"),
            show_vertices_labels=show_vertices_labels,
            signed=compute_polarity,   # ← coloration bleu/rouge si polarité activée
        )
    if save_graphml:
        save_graphml_file(os.path.join(output_dir, "graphml.xml"), to_graphml(graph))

    return to_graphml(graph, pretty=False)


def is_filename_well_formed(filename: str) -> bool:
    base_name = os.path.basename(filename)
    match = re.match(r"([a-zA-Z]+)[._-]chapter[_-](\d+)\.txt$", base_name)
    return match is not None


def main():
    parser = argparse.ArgumentParser(
        description="Tokenize a text file into sentences and words. a classic use will be `networker -gilm`."
    )
    config_argparse(parser)
    parser.add_argument("--text", "-t", type=str, dest="input_file", action="append")
    parser.add_argument("--dir", "-d", type=str, dest="input_dir", action="append")
    parser.add_argument("--save-intermediate", "-i", action="store_true")
    parser.add_argument("--save-graph-image", "-g", action="store_true")
    parser.add_argument("--show-vertices-labels", "-l", action="store_true")
    parser.add_argument("--save-unknow-verb", "-u", action="store_true")
    parser.add_argument("--save-graphml", "-m", action="store_true")
    parser.add_argument("--csv", "-c", action="store_true")
    parser.add_argument(
        "--no-polarity", action="store_true",
        help="Désactiver le calcul de polarité (plus rapide, réseau non signé)."
    )
    args = parser.parse_args()

    config_logger(args)
    init_nltk()

    df_dict = {"ID": [], "graphml": []}

    if not args.input_file and not args.input_dir:
        Logger.warning("no input files or directories provided. taking texts from ./text_dataset/ by default.")
        args.input_dir = ["./text_dataset/"]

    input_files = args.input_file if args.input_file else []
    if args.input_dir:
        for input_dir in args.input_dir:
            for fname in os.listdir(input_dir):
                if is_filename_well_formed(fname):
                    input_files.append(os.path.join(input_dir, fname))
                else:
                    Logger.warning(f"Skipping file with unexpected name format: {fname}")

    def _sort_key(path: str):
        code, chap = get_book_chapter(path)
        return (0 if code == "paf" else 1, chap)

    input_files = sorted(input_files, key=_sort_key)

    # Réinitialiser le registre de polarité à chaque changement de livre
    current_book = None

    for input_file in input_files:
        book_code, _ = get_book_chapter(input_file)
        if book_code != current_book:
            if current_book is not None:
                Logger.info(f"Changement de livre : sauvegarde et reset du registre de polarité")
                save_pairs()   # sauvegarder les paires apprises sur ce livre
            reset_book_scores()
            current_book = book_code
        Logger.info(f"Processing file: {input_file}")
        graphml = build_characters_graph(
            input_file,
            save_intermediate=args.save_intermediate,
            save_graph_image=args.save_graph_image,
            show_vertices_labels=args.show_vertices_labels,
            save_unknow_verb="output/unknown_verbs.txt" if args.save_unknow_verb else None,
            save_graphml=args.save_graphml,
            compute_polarity=not args.no_polarity,
        )
        book_code, chapter_number = get_book_chapter(input_file)
        if args.csv:
            df_dict["ID"].append(f"{book_code}{chapter_number}")
            df_dict["graphml"].append(graphml)

    # Sauvegarder les paires auto-apprises du dernier livre
    save_pairs()

    if args.csv:
        df = pd.DataFrame(df_dict)
        df["book"] = df["ID"].str[:3]
        df["chap"] = df["ID"].str[3:].astype(int)
        df["book_order"] = df["book"].map({"paf": 0, "lca": 1})
        df = df.sort_values(["book_order", "chap"])
        df = df[["ID", "graphml"]]
        df.to_csv("./output/my_submission.csv", index=False)
        Logger.info("Wrote output csv to output/my_submission.csv")


if __name__ == "__main__":
    main()