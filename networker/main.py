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


# logger setup
Logger.set_module("main")


# ===== Constants =====
# Thresholds for promotion/demotion of proper-noun candidates
PROMOTE_MIN_COUNT = 2       # min proper observations to consider a token
PROMOTE_MIN_SCORE = 0.7    # proper / (proper + nonproper_lower)
PROMOTE_MIN_BIGRAM = 1      # min observations for a proper bigram

DEMOTE_MIN_COUNT = 1        # minimum times seen in lowercase to be reliable
DEMOTE_MAX_RATIO = 0.15       # if proper/(proper+nonproper) < 0.3 => demoted

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
    Logger.info(f"Loaded {nb_sentences} sentences from {input_file}")
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

    Logger.info(f"Auto-demoted: {len(auto_demote_tokens)} tokens\nfirst 10: {list(auto_demote_tokens)[:10]}")

    promoted_bigrams = {bg for bg, c in proper_bigram_count.items() if c >= PROMOTE_MIN_BIGRAM}
    return promoted_tokens, promoted_bigrams, auto_demote_tokens



# --------- PASS B: final tagging ---------
def tag_sentence_tokens(prepared: list[dict[str, int | str | bool | list[str]]], promoted_tokens: set, promoted_bigrams: set, auto_demote_tokens: set, store_unknow_verb : str|None = None) -> list[dict]:
    result = []
    potential_persons = defaultdict(int)  # Track potential persons
    
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
                    word = words_list_dict[-1]["word"]
                    word = word.strip("-")
                    try:
                        verb_data = get_verb_data(words_list_dict[-1]["word"], words_list_dict, j)
                    except ValueError as e:
                        # don't merge if the verb not found, mark the second element as ADJECTIVE instead
                        words_list_dict[-1]["word"] = words_list_dict[-1]["word"].rsplit(" ", 1)[0]
                        words_list_dict.append({
                            "word": tok,
                            "position": j,
                            "type": TokenType.ADJECTIVE.value
                        })
                        prev_token = words_list_dict[-2]
                        Logger.debug(f"{e}\ndefaulting to:\n\t{prev_token['word']:10} {prev_token['type']}\n\t{tok:10} adjective")
                        if store_unknow_verb:
                            append_to_file(store_unknow_verb, words_list_dict[-1]['word'])
                            Logger.debug(f"Stored unknown verb '{words_list_dict[-1]['word']}' to {store_unknow_verb}")
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
                    noun_type, reason = guess_noun_type(tokens, words_list_dict, j, token_type)
                    token_data["noun_type"] = noun_type.value
                    token_data["noun_type_reason"] = reason
                    
                    # Log potential persons
                    if noun_type.value == "person":
                        potential_persons[tok] += 1
                    elif token_type == TokenType.PROPER_NOUN:
                        # Log proper nouns that weren't classified as persons
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
    
    # Log summary of potential persons
    Logger.info(f"Found {len(potential_persons)} potential person entities")
    sorted_persons = sorted(potential_persons.items(), key=lambda x: x[1], reverse=True)
    Logger.debug(f"Top 20 potential persons:\n" + "\n".join([f"  {name}: {count}" for name, count in sorted_persons[:20]]))
    
    return result

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
    """
    Extract book code and chapter number from input file path.
    Assumes input file is named like 'code_chapter.txt', e.g. 'paf.chapter_12.txt'.
    """
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} not found.")
    
    base_name = os.path.basename(input_file)
    match = re.match(r"([a-zA-Z]+)[._-]chapter[_-](\d+)\.txt$", base_name)
    if not match:
        raise ValueError(f"Input file name {base_name} does not match expected pattern '[code].chapter_[number].txt'")
    book_code = match.group(1)
    chapter_number = int(match.group(2))
    return book_code, chapter_number
    

# =============================================================================
# Blacklist : entités qui ne peuvent PAS être des personnages.
# Guidelines du sujet : ethnonymes, lieux, artefacts OCR exclus.
# =============================================================================
PERSON_BLACKLIST: frozenset[str] = frozenset({
    # ── Lieux (PAF + LCA) ────────────────────────────────────────────────────
    "trantor", "terminus", "helicon", "anacreon", "mycogene", "mycogène",
    "kalgan", "korell", "askone", "smyrno", "sayshell", "gaia",
    "spacetown", "aurora", "solaria", "comporellon",
    # ── Ethnonymes / démonymes (explicitement exclus par les guidelines) ──────
    "spaciens", "spacien", "spacienne", "spaciennes",
    "terriens", "terrien", "terrienne",
    "galactiques", "galactique",
    "trantorien", "trantoriens", "trantorienne",
    "Mycogéniens", "mycogénien", "mycogénienne", "mycogéniennes",
    # ── Entités non-personnages Fondation ─────────────────────────────────────
    "encyclopaedia galactica", "encyclopaedia", "galactica",
    "plan seldon", "plan", "empire galactique", "empire",
    "premiere fondation", "seconde fondation", "fondation",
    "Goutte-de-Pluie Quarante", "goutte-de-pluie quarante", "goutte de pluie quarante", "goutte-de-pluie", "goutte de pluie",
    # ── Verbes / syntagmes mal classifiés ─────────────────────────────────────
    "exact", "souligner", "précéda", "le précéda",
    "cette croyance", "affirmer", "sembler",
    "etant", "étant", "voila", "voilà",
    "mis",           # participe passé de "mettre" — pas Ebling Mis
    "des principes", "votre rythme",
    # ── Titres génériques (pas des personnages spécifiques) ──────────────────
    "monsieur", "madame", "mademoiselle",
    "frere", "frère",   # titre générique dans PAF Mycogen
    "professeur",
    # ── Objets / concepts mal classifiés ─────────────────────────────────────
    "livre",            # objet, pas un personnage
    "robot",            # catégorie, pas un nom propre
    # ── Artefacts OCR ────────────────────────────────────────────────────────
    "― sire ‖", "sire ‖",
    # ── Lieux non-FR et organisations détectés par spaCy ─────────────────────
    "new york", "new york city", "chicago", "washington",
    "police", "la police", "garde",
    "t- e-r-r-a", "terra",  # artefact OCR de TERRA (lieu)
    # ── Dynasties / organisations ─────────────────────────────────────────────
    "dynastie entun",
    # ── Verbes à l'impératif mal classifiés (fréquent dans LCA) ──────────────
"ecoute", "ecoutez", "ecoutez-", "reponds", "commandez",
"etait-", "tais-toi",
# ── Lieux US détectés par spaCy ──────────────────────────────────────────
"new jersey",
# ── Organisations / mouvements ───────────────────────────────────────────
"medievalistes", "médiévalistes", "subdivisions ia",
# ── Syntagmes mal classifiés ─────────────────────────────────────────────
"ciel", "votre desir", "votre désir", "affaire sarton", "cette affaire", "cette affaire sarton",
 # ── Lieux PAF (secteurs/planètes) ────────────────────────────────────────
"helicon", "hélicon",       # planète natale de Seldon
"billibotton",              # quartier de Dahl
"dahl",                     # secteur de Trantor
"streeling",                # secteur de Trantor
"sacratorium",              # lieu Mycogène
"microferme",               # lieu/objet

# ── Ethnonymes PAF ────────────────────────────────────────────────────────
"mycogeniens", "mycogéniens",
"kanite",

# ── Titres génériques seuls (sans nom propre) ─────────────────────────────
"sergent", "maire",
"maitresse", "maîtresse",   # seul, sans nom
"soeur", "sœur", "soeurs", "sœurs",

# ── Verbes mal classifiés ────────────────────────────────────────────────
"neutralisez", "concevoir",

# ── Syntagmes nominaux ───────────────────────────────────────────────────
"sa culture et", "les predictions et", "les prédictions et",
"toute apparence", "de maison", "la tradition", "le rite",
"tite dame",

# ── Artefacts OCR ────────────────────────────────────────────────────────
"maitre-", "maître-", "f- frere", "f- frère",
"bande-", "ba-lee", "da- nee", "e.g",
"seldon acquiesça", "sauvetage",

# ── Autres faux positifs ─────────────────────────────────────────────────
"historienne", "renégat", "renegat",
})


def _is_blacklisted(name: str) -> bool:
    """
    Retourne True si le nom doit être exclu des personnages.
    1. Contient un saut de ligne  → artefact OCR garanti.
    2. Longueur > 50 caractères   → artefact probable.
    3. Dans PERSON_BLACKLIST       → entité non-personne connue.
    4. Uniquement non-alphabétique → ponctuation/chiffres.
    """
    if "\n" in name:
        return True
    if len(name) > 50:
        return True
    if not any(c.isalpha() for c in name):
        return True
    return name.lower().strip() in PERSON_BLACKLIST


def filter_word_count(word_count: dict[str, int]) -> dict[str, int]:
    """Supprime les entrées non-personnes du word_count."""
    filtered = {n: c for n, c in word_count.items() if not _is_blacklisted(n)}
    removed = set(word_count) - set(filtered)
    if removed:
        Logger.info(f"Blacklist: {len(removed)} entrées supprimées → {sorted(removed)}")
    return filtered


def clean_ocr_text(text: str) -> str:
    """
    Répare les noms fragmentés par des sauts de ligne OCR avant d'envoyer à spaCy.
    Exemples :
      "Robot Daneel\\nOlivaw"  → "Robot Daneel Olivaw"
      "Eto\\nDemerzel"         → "Eto Demerzel"

    Stratégie : remplacer les \\n qui sont entre deux tokens qui commencent
    par une majuscule (caractéristique d'un nom propre fragmenté) par un espace.
    Les vrais sauts de paragraphe (\\n\\n) sont préservés.
    """
    # Préserver les doubles sauts de ligne (fins de paragraphe)
    text = re.sub(r'\n\n+', '\x00', text)
    # Réparer les noms propres fragmentés : lettre majuscule, \n, lettre majuscule
    text = re.sub(r'([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç]*)\n([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ])',
                  r'\1 \2', text)
    # Restaurer les vrais sauts de paragraphe
    text = text.replace('\x00', '\n\n')
    return text


def extract_persons_spacy(text: str) -> dict[str, int]:
    """
    NER secondaire via spaCy sur le texte NETTOYÉ (OCR réparé).
    Récupère les entités PER ratées par le pipeline custom.
    Applique la blacklist avant injection.
    """
    nlp = get_nlp()
    # Nettoyer les artefacts OCR avant analyse
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
    """
    Fusionne deux word_counts.
    Les entités nouvelles de secondary ne sont ajoutées que si count >= min_spacy_count.
    """
    merged = dict(primary)
    for name, count in secondary.items():
        if name in merged:
            merged[name] += count
        elif count >= min_spacy_count:
            merged[name] = count
    return dict(sorted(merged.items(), key=lambda x: x[1], reverse=True))


def build_characters_graph(input_file: str,
                            save_intermediate: bool = False,
                            save_graph_image: bool = False,
                            show_vertices_labels: bool = False,
                            save_unknow_verb: str | None = None,
                            save_graphml: bool = False
                            ) -> str:
    book_code, chapter_number = get_book_chapter(input_file)

    sentences_by_pages = load_text(input_file)
    prepared = prepare_sentences(sentences_by_pages)
    token_counts = learn_proper_token_stats(prepared)
    promoted_data = compute_promotion_demotion(*token_counts)
    result = tag_sentence_tokens(prepared, *promoted_data, save_unknow_verb)

    result = identify_subject_for_pronoun(result)
    result = merge_determiners_nouns(result)

    # NER primaire : pipeline custom (word_type.py)
    word_count = count_occurrences(result)
    Logger.info(f"NER custom: {len(word_count)} personnages")

    # Filtre blacklist
    word_count = filter_word_count(word_count)

    # NER secondaire : spaCy sur texte OCR nettoyé
    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()
    spacy_wc = extract_persons_spacy(raw_text)

    # Fusion (entités spaCy nouvelles uniquement si vues >= 2 fois)
    word_count = merge_word_counts(word_count, spacy_wc, min_spacy_count=2)
    Logger.info(f"NER fusionné: {len(word_count)} personnages")

    # Résolution d'alias unifiée
    aliases = resolve_aliases(list(word_count.keys()), word_count=word_count)
    canonical_names = [group[0] for group in aliases]

    link_table = build_links_file(
        input_file,
        canonical_names,
        aggregated=True,
        window=25,   # augmenté de 25 → 50 pour améliorer le rappel des arêtes
        min_count=1,
        external_alias_map={name: name for name in canonical_names},
    )

    output_dir = get_output_dir(book_code, chapter_number)

    if save_intermediate:
        save_structure_data(aliases, output_dir, "aliases")
        save_structure_data(link_table, output_dir, "link_table")
        save_structure_data(result, output_dir, "parsed_sentences")
        save_structure_data(word_count, output_dir, "word_count")

    graph = create_graph(aliases, link_table)

    if save_graph_image:
        save_img_graph(graph, os.path.join(output_dir, "graph.png"),
                       show_vertices_labels=show_vertices_labels)
    if save_graphml:
        save_graphml_file(os.path.join(output_dir, "graphml.xml"), to_graphml(graph))

    return to_graphml(graph, pretty=False)


def is_filename_well_formed(filename: str) -> bool:
    base_name = os.path.basename(filename)
    match = re.match(r"([a-zA-Z]+)[._-]chapter[_-](\d+)\.txt$", base_name)
    return match is not None


def main():
    parser = argparse.ArgumentParser(description="Tokenize a text file into sentences and words. a classic use will be `networker -gilm`. This will generate all graphs for the input texts, and save all intermediate data structures.")
    config_argparse(parser)
    parser.add_argument("--text", "-t", type=str, help="Path to the input text file.", dest="input_file", action="append")
    parser.add_argument("--dir", "-d", type=str, help="Path to a folder containing text to process.", dest="input_dir", action="append")
    parser.add_argument("--save-intermediate", "-i", action="store_true", help="Save intermediate data structures to output directory.")
    parser.add_argument("--save-graph-image", "-g", action="store_true", help="Save graph image to output directory.")
    parser.add_argument("--show-vertices-labels", "-l", action="store_true", help="Show vertex labels on the saved graph image. Have no effect if --save-graph-image is not set.")
    parser.add_argument("--save-unknow-verb", "-u", help="Store unknown verbs encountered during tagging to 'output/unknown_verbs.txt'.", action="store_true")
    parser.add_argument("--save-graphml", "-m", help="Save the graph in GraphML format to the output directory.", action="store_true")
    parser.add_argument("--csv", "-c", help="Append results to a summary CSV file 'output/graphs_summary.csv'.", action="store_true")
    args = parser.parse_args()
    
    config_logger(args)
    
    init_nltk() # differ nltk initialization to after parsing arguments, to avoid unnecessary downloads if help is requested
    
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
    # Sort input files by (book_code, chapter_number) so CSV rows are ordered
    def _sort_key(path: str):
        code, chap = get_book_chapter(path)
        book_order = 0 if code == "paf" else 1
        return (book_order, chap)
    input_files = sorted(input_files, key=_sort_key)
    for input_file in input_files:
        Logger.info(f"Processing file: {input_file}")
        graphml = build_characters_graph(input_file,
                                        save_intermediate=args.save_intermediate,
                                        save_graph_image=args.save_graph_image,
                                        show_vertices_labels=args.show_vertices_labels,
                                        save_unknow_verb="output/unknown_verbs.txt" if args.save_unknow_verb else None,
                                        save_graphml=args.save_graphml
                                        )
        book_code, chapter_number = get_book_chapter(input_file)
        
        #TODO add to the general result file using the book_code and chapter_number
        if args.csv:
            # append_to_csv(book_code, chapter_number, graphml)
            df_dict["ID"].append(f"{book_code}{chapter_number}")
            df_dict["graphml"].append(graphml)
    if args.csv:
        # Build DataFrame from collected graphs
        df = pd.DataFrame(df_dict)
        # Extract book code (first 3 chars) and chapter number (rest as int) for natural sort
        df["book"] = df["ID"].str[:3]
        df["chap"] = df["ID"].str[3:].astype(int)
        df["book_order"] = df["book"].map({"paf": 0, "lca": 1})

        df = df.sort_values(["book_order", "chap"])

        df = df[["ID", "graphml"]]
        # Write CSV without index (Kaggle expects only ID,graphml)
        df.to_csv("./output/my_submission.csv", index=False)
        Logger.info("Wrote output csv to output/my_submission.csv")


if __name__ == "__main__":
    main()