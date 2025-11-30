import time
import argparse as ap
from typing import Callable
import shlex
import json
import readline
import inspect

from gamuLogger import Logger, config_argparse, config_logger
Logger.set_module("verb cli")

from .verbs_engine import VerbTree, VerbData, mood_map, tense_map, pronoun_map

readline.set_history_length(100)

tree = VerbTree()
tree_filename = ""
edited = False
auto_save = False

COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "yellow": "\033[93m",
    "reset": "\033[0m"
}

color = "\033[92m"

def set_autosave(value_str: str):
    """Set auto-save option. Usage: autosave <true|false>"""
    if value_str.lower() in ["true", "1", "yes"]:
        value = True
    else:
        value = False
    global auto_save
    auto_save = value
    print(f"Auto-save set to {auto_save}")
    
    
def remove_articles(infinitive: str) -> str:
    """Remove leading articles from an infinitive verb."""
    articles = ["je ", "tu ", "il ", "elle ", "on ", "nous ", "vous ", "ils ", "elles ", "il/elle ", "il/elle/on ", "ils/elles ", "j'"]
    articles += ["que je ", "que tu ", "qu'il ", "qu'elle ", "qu'on ", "que nous ", "que vous ", "qu'ils ", "qu'elles ", "qu'il/elle ", "qu'il/elle/on ", "qu'ils/elles ", "que j'"]
    infinitive_lower = infinitive.lower()
    for article in articles:
        if infinitive_lower.startswith(article):
            return infinitive[len(article):].strip()
    return infinitive

 
############################################# Loading #############################################

def load(file_path: str, json: bool = False):
    """Load a verb tree from a file. Usage: load <file_path> [--json]"""
    global tree
    global tree_filename
    if json:
        timer = time.time()
        tree = VerbTree.load_json(file_path)
        print(f"Verb tree loaded in json format from {file_path} in {time.time() - timer:.6f} seconds")
    else:
        timer = time.time()
        tree = VerbTree.load(file_path)
        print(f"Verb tree loaded from {file_path} in {time.time() - timer:.6f} seconds")
    tree_filename = file_path


########################################### Operations ############################################

def list_verbs(len : int = -1):
    """List all infinitive verbs in the tree. Usage: list [--len <number>]"""
    infinitives = tree.list_verbs()
    if len > 0:
        infinitives = infinitives[:len]
    for infinitive in infinitives:
        print(infinitive)
        
def head(len : int = 10):
    """Display the first n verbs in the tree. Usage: head [--len <number>]"""
    count = 0
    for form, data in tree:
        print(f"{form:24} -> {data}")
        count += 1
        if count >= len:
            break

def tail(len : int = 10):
    """Display the last n verbs in the tree. Usage: tail [--len <number>]"""
    all_verbs = list(tree)
    for form, data in all_verbs[-len:]:
        print(f"{form:24} -> {data}")
    
def size():
    """Display the size of the verb tree. Usage: size"""
    print(f"Verb tree size: {len(tree)} nodes, {tree.get_verb_number()} verbal forms, {len(tree.list_verbs())} infinitive verbs")
 
def health(only_errors: bool = False):
    """Perform a health check on the verb tree. Usage: health [--only_errors]"""
    data = [(f, i) for f, i in tree]
    infinitive_count = {}
    for f, i in data:
        infinitive = i.infinitive
        if infinitive not in infinitive_count:
            infinitive_count[infinitive] = 0
        infinitive_count[infinitive] += 1
    for infinitive, count in sorted(infinitive_count.items()):
        if count == 97:
            if only_errors:
                continue
            color = "\033[92m"
        else:
            color = "\033[91m"
        print(f"{infinitive}: {color}{count}\033[0m")

def has(verb_to_check: str):
    """Check if a verb exists in the tree. Usage: has <verb>"""
    exists = tree.search(verb_to_check)
    if exists:
        print(f"The verb '{verb_to_check}' exists in the tree.")
    else:
        print(f"The verb '{verb_to_check}' does NOT exist in the tree.")

def get(verb_to_get: str, strict: bool = False):
    """Get conjugation data for a verb. Usage: get <verb> [--strict <true|false>]"""
    conjugations = tree.get(verb_to_get, strict=strict)
    if conjugations:
        print(f"Conjugation data for '{verb_to_get}':")
        for conjugation in conjugations:
            print(f"  {conjugation}")
    else:
        print(f"No conjugation data found for '{verb_to_get}'.")

def lookup(infinitive_to_lookup: str, mood: str = "", tense: str = "", pronoun: str = ""):
    """Lookup all conjugated forms for an infinitive verb. Usage: lookup <infinitive> [--mood <mood>] [--tense <tense>] [--pronoun <pronoun>]"""
    forms = [(f, i) for f, i in tree if i.infinitive == infinitive_to_lookup]
    if forms:
        print(f"Conjugated forms for infinitive '{infinitive_to_lookup}':")
        for form, data in forms:
            if mood and data.mood != mood_map[mood]:
                continue
            if tense and data.tense != tense_map[tense]:
                continue
            if pronoun and data.pronoun != pronoun_map[pronoun]:
                continue
            print(f"\t{form:24} -> {data}")
    else:
        print(f"No conjugated forms found for infinitive '{infinitive_to_lookup}'.")

############################################ Editing ############################################

def extend(file_path: str):
    """Extend the verb tree with predefined data from a file. Usage: extend <file_path>"""
    global edited
    timer = time.time()

    with open(file_path, "r", encoding="utf-8") as f:
        verb_data = json.load(f)
    count = 0
    for entry in verb_data:
        conjugated_form = entry[0]
        infinitive = entry[1]
        mood = mood_map[entry[2]]
        tense = tense_map[entry[3]]
        pronoun = pronoun_map[entry[4]]
        tree.insert(conjugated_form, VerbData(infinitive, mood, tense, pronoun))
        count += 1
    print(f"Extended verb tree with {count} entries from {file_path} in {time.time() - timer:.6f} seconds")
    edited = True
    if auto_save:
        tree.save(tree_filename)

def insert(infinitive: str, mood: str, tense: str, pronoun: str, form: str):
    """Insert a new conjugated verb form into the tree. Usage: insert <infinitive> <mood> <tense> <pronoun> <form>"""
    global edited
    tree.insert(form, VerbData(infinitive, mood_map[mood], tense_map[tense], pronoun_map[pronoun]))
    edited = True
    if auto_save:
        tree.save(tree_filename)

def harmonize(simulate : bool = False):
    """Harmonize the verb tree by converting all forms and infinitives to lowercase. Usage: harmonize [--simulate]"""
    global edited
    global tree
    
    # put all verbs, conjugated forms and infinitives, to lowercase
    timer = time.time()
    new_tree = VerbTree()
    count = 0
    for form, data in tree:
        new_form = form.lower()
        new_form = remove_articles(new_form)
        new_infinitive = data.infinitive.lower()
        if new_form != form or new_infinitive != data.infinitive:
            print(f"Harmonizing: '{form}' -> '{new_form}', '{data.infinitive}' -> '{new_infinitive}'")
            if not simulate:
                edited = True
        new_data = VerbData(new_infinitive, data.mood, data.tense, data.pronoun)
        new_tree.insert(new_form, new_data)
        count += 1
    if simulate:
        print(f"Simulated harmonization to lowercase with {count} entries in {time.time() - timer:.6f} seconds")
    else:
        tree = new_tree
        print(f"Harmonized verb tree to lowercase with {count} entries in {time.time() - timer:.6f} seconds")
        if auto_save:
            tree.save(tree_filename)
    
def sanitize(simulate: bool = False):
    """Sanitize the verb tree by transforming variable forms into separate variants. Usage: sanitize [--simulate]"""
    global edited
    global tree
    # transform all variable forms (those with parentheses) to separated variants
    # e.g. "soyons rendu(e)s" -> "soyons rendus" and "soyons rendue"
    # e.g. "fûtes allé(e)(s)" -> "fûtes allé", "fûtes allés", "fûtes allée", "fûtes allées"
    timer = time.time()
    new_tree = VerbTree()
    count = 0
    for form, data in tree:
        if "(" in form and ")" in form:
            base_form = ""
            i = 0
            variants = [""]
            while i < len(form):
                if form[i] == "(":
                    j = i + 1
                    optional_part = ""
                    while j < len(form) and form[j] != ")":
                        optional_part += form[j]
                        j += 1
                    # create new variants with and without the optional part
                    new_variants = []
                    for variant in variants:
                        new_variants.append(variant)  # without optional part
                        new_variants.append(variant + optional_part)  # with optional part
                    variants = new_variants
                    i = j + 1
                else:
                    for k in range(len(variants)):
                        variants[k] += form[i]
                    i += 1
            for variant in variants:
                variant = variant.strip()
                if variant:
                    new_tree.insert(variant, data)
                    print(f"Sanitizing: '{form}' -> '{variant}'")
                    if not simulate:
                        edited = True
        else:
            new_tree.insert(form, data)
        count += 1
    if simulate:
        print(f"Simulated sanitization of variable forms with {count} entries in {time.time() - timer:.6f} seconds")
    else:
        tree = new_tree
        print(f"Sanitized variable forms in verb tree with {count} entries in {time.time() - timer:.6f} seconds")
        if auto_save:
            tree.save(tree_filename)


def remove_duplicates(simulate: bool = False):
    """Remove duplicate verb entries from the tree. Usage: remove_duplicates [--simulate]"""
    # remove duplicate verbs in the tree. a verb is duplicate if it has the same conjugated form and infinitive as another item
    global edited
    global tree
    timer = time.time()
    new_tree = VerbTree()
    count = 0
    seen : dict[str, tuple[str, VerbData]] = {}
    for form, data in tree:
        identifier = (f"{form}{data.infinitive}{data.mood.name}{data.tense.name}{data.pronoun.name}")
        if identifier not in seen:
            new_tree.insert(form, data)
            seen[identifier] = (form, data)
            count += 1
        else:
            print(f"Removing duplicate: '{form}' with infinitive '{data.infinitive}'")
            if not simulate:
                edited = True
    if simulate:
        print(f"Simulated removal of duplicates, new tree would have {count} entries in {time.time() - timer:.6f} seconds")
    else:
        tree = new_tree
        print(f"Removed duplicates, new tree has {count} entries in {time.time() - timer:.6f} seconds")
        if auto_save:
            tree.save(tree_filename)
    
############################################# Saving ##############################################        


def save(file_path: str = "", json: bool = False):
    """Save the verb tree to a file. Usage: save [file_path] [--json]"""
    if file_path == "":
        file_path = tree_filename
    if json:
        timer = time.time()
        tree.save_json(file_path)
        print(f"Verb tree saved in json format to {file_path} in {time.time() - timer:.6f} seconds")
    else:
        timer = time.time()
        tree.save(file_path)
        print(f"Verb tree saved to {file_path} in {time.time() - timer:.6f} seconds")
    global edited
    edited = False

def export_uncompressed(file_path: str):
    """Export the verb tree to an uncompressed file. Usage: export_uncompressed <file_path>"""
    timer = time.time()
    tree.save_uncompressed(file_path)
    print(f"Verb tree exported uncompressed to {file_path} in {time.time() - timer:.6f} seconds")


OPERATIONS : dict[str, Callable[..., None]] = {
    "load": load,
    "list": list_verbs,
    "head": head,
    "tail": tail,
    "size": size,
    "health": health,
    "has": has,
    "get": get,
    "lookup": lookup,
    "extend": extend,
    "insert": insert,
    "harmonize": harmonize,
    "sanitize": sanitize,
    "remove_duplicates": remove_duplicates,
    "save": save,
    "export_uncompressed": export_uncompressed,
    "autosave": set_autosave,
}

def generate_argparser_for_command(command: str) -> ap.ArgumentParser:
    func = OPERATIONS.get(command)
    if func is None:
        raise ValueError(f"No function found for command '{command}'")
    parser = ap.ArgumentParser(exit_on_error=False, add_help=False)
    for param_name, param_data in inspect.signature(func).parameters.items():
        if param_data.default is param_data.empty: # no default value
            parser.add_argument(param_name, type=param_data.annotation)
        else:
            if param_data.annotation == bool:
                parser.add_argument(f"--{param_name}", action="store_true" if param_data.default is False else "store_false")
            else:
                parser.add_argument(f"--{param_name}", type=param_data.annotation, default=param_data.default)
    return parser

def mainloop():
    while True:
        if auto_save:
            color = COLORS["blue"]
        elif edited:
            color = COLORS["yellow"]
        else:
            color = COLORS["green"]
        try:
            full_cmd = input(f"{color}{tree_filename.split("/")[-1]}> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print() #new line
            break
        try:
            tokens = shlex.split(full_cmd)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue
        if not tokens:
            continue
        cmd = tokens[0]
        args = tokens[1:]

        if cmd == "exit" or cmd == "quit":
            if edited:
                if auto_save:
                    tree.save(tree_filename)
                    print(f"Changes auto-saved to {tree_filename}.")
                else:
                    confirm = input("You have unsaved changes. Quit without saving? (y/n): ").strip().lower()
                    if confirm != "y":
                        return
            break
        elif cmd == "help":
            if args and args[0] in OPERATIONS:
                func = OPERATIONS[args[0]]
                if func.__doc__:
                    print(func.__doc__)
                else:
                    print(f"No help available for '{args[0]}'")
            else:
                print("Available commands:")
                for command in OPERATIONS.keys():
                    print(f"  - {command}")
                print("Type 'help <command>' for more details on a specific command.")
        elif cmd in OPERATIONS:
            parser = generate_argparser_for_command(cmd)
            try:
                parsed_args = parser.parse_args(args)
                OPERATIONS[cmd](**vars(parsed_args))
            except Exception as e:
                print(f"Error executing command '{cmd}': {e.__class__.__name__}: {e}")
        else:
            print(f"Unknown command: {cmd}")
    print("Bye.")

def main():
    argparser = ap.ArgumentParser(description="Verb Tree CLI")
    argparser.add_argument("file", type=str, help="Path to the verb tree file to load", default=None, nargs="?")
    argparser.add_argument("--json", action="store_true", help="Load the verb tree in JSON format")
    
    config_argparse(argparser)
    args = argparser.parse_args()
    config_logger(args)
    
    print("Welcome to the Verb Tree CLI. Type 'help' for a list of commands.")

    if args.file:
        load(args.file, json=args.json)
    
    mainloop()
    
if __name__ == "__main__":
    main()