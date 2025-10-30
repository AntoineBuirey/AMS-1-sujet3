from verbs_engine import VerbTree, VerbData, mood_map, tense_map, pronoun_map
import time
import argparse as ap
import readline
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


autosave_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
autosave_argparser.add_argument("value_str", type=str, help="Set auto-save to true or false")

def set_autosave(value_str: str):
    if value_str.lower() in ["true", "1", "yes"]:
        value = True
    else:
        value = False
    global auto_save
    auto_save = value
    print(f"Auto-save set to {auto_save}")

 
############################################# Loading #############################################

load_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
load_argparser.add_argument("file_path", type=str, help="Path to the verb tree file")
load_argparser.add_argument("--json", action="store_true", help="Load the verb tree in JSON format")

def load(file_path: str, json: bool = False):
    global tree
    global tree_filename
    tree_filename = file_path
    if json:
        timer = time.time()
        tree = VerbTree.load_json(file_path)
        print(f"Verb tree loaded in json format from {file_path} in {time.time() - timer:.6f} seconds")
    else:
        timer = time.time()
        tree = VerbTree.load(file_path)
        print(f"Verb tree loaded from {file_path} in {time.time() - timer:.6f} seconds")


########################################### Operations ############################################

list_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)

def list_verbs():
    print(tree.list_verbs())
    

size_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
    
def size():
    print(f"Verb tree size: {len(tree)} nodes, {tree.get_verb_number()} verbal forms, {len(tree.list_verbs())} infinitive verbs")
    
health_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
health_argparser.add_argument("--only_errors", action="store_true", help="Show only errors in the health check")
    
def health(only_errors: bool = False):
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

has_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
has_argparser.add_argument("verb_to_check", type=str, help="The verb to check for existence in the tree")

def has(verb_to_check: str):
    exists = tree.search(verb_to_check)
    if exists:
        print(f"The verb '{verb_to_check}' exists in the tree.")
    else:
        print(f"The verb '{verb_to_check}' does NOT exist in the tree.")

get_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
get_argparser.add_argument("verb_to_get", type=str, help="The verb to get conjugation data for")    

def get(verb_to_get: str):
    conjugations = tree.get(verb_to_get)
    if conjugations:
        print(f"Conjugation data for '{verb_to_get}':")
        for conjugation in conjugations:
            print(f"  {conjugation}")
    else:
        print(f"No conjugation data found for '{verb_to_get}'.")

lookup_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
lookup_argparser.add_argument("infinitive_to_lookup", type=str, help="The infinitive verb to lookup conjugated forms for")
lookup_argparser.add_argument("--mood", type=str, help="Filter by mood", default=None)
lookup_argparser.add_argument("--tense", type=str, help="Filter by tense", default=None)
lookup_argparser.add_argument("--pronoun", type=str, help="Filter by pronoun", default=None)

def lookup(infinitive_to_lookup: str, mood: str|None = None, tense: str|None = None, pronoun: str|None = None):
    forms = [(f, i) for f, i in tree if i.infinitive == infinitive_to_lookup]
    if forms:
        print(f"Conjugated forms for infinitive '{infinitive_to_lookup}':")
        for form, data in forms:
            if mood and data.mood.name != mood.upper():
                continue
            if tense and data.tense.name != tense.upper():
                continue
            if pronoun and data.pronoun.name != pronoun.upper():
                continue
            print(f"\t{form:24} -> {data}")
    else:
        print(f"No conjugated forms found for infinitive '{infinitive_to_lookup}'.")

############################################ Editing ############################################

extend_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)

def extend():
    from verb_data import DATA
    for verb in DATA:
        tree.insert(verb[0], VerbData(verb[1], mood_map[verb[2]], tense_map[verb[3]], pronoun_map[verb[4]]))
    
    infinitive = set()
    for verb in DATA:
        infinitive.add(verb[1])
    print(f"inserted {len(DATA)} items from verb_data.py\nverbs added:\n\t{"\n\t".join(sorted(infinitive))}")
    if auto_save:
        tree.save(tree_filename)


insert_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
insert_argparser.add_argument("infinitive", type=str, help="The infinitive form of the verb")
insert_argparser.add_argument("mood", type=str, help="The mood of the verb")
insert_argparser.add_argument("tense", type=str, help="The tense of the verb")
insert_argparser.add_argument("pronoun", type=str, help="The pronoun of the verb")
insert_argparser.add_argument("form", type=str, help="The conjugated form of the verb")

def insert(infinitive: str, mood: str, tense: str, pronoun: str, form: str):
    global edited
    tree.insert(form, VerbData(infinitive, mood_map[mood], tense_map[tense], pronoun_map[pronoun]))
    edited = True
    if auto_save:
        tree.save(tree_filename)
    
    
############################################# Saving ##############################################        

save_argparser = ap.ArgumentParser(exit_on_error=False, add_help=False)
save_argparser.add_argument("file", type=str, help="Path to save the verb tree file", default=None)
save_argparser.add_argument("--json", action="store_true", help="Save the verb tree in JSON format")

def save(file: str|None = None, json: bool = False):
    if file is None:
        file = tree_filename
    if json:
        timer = time.time()
        tree.save_json(file)
        print(f"Verb tree saved in json format to {file} in {time.time() - timer:.6f} seconds")
    else:
        timer = time.time()
        tree.save(file)
        print(f"Verb tree saved to {file} in {time.time() - timer:.6f} seconds")
    global edited
    edited = False


OPERATIONS = {
    "load": load,
    "list": list_verbs,
    "size": size,
    "health": health,
    "has": has,
    "get": get,
    "lookup": lookup,
    "extend": extend,
    "insert": insert,
    "save": save,
    "autosave": set_autosave,
}

HELPS = {
    "load": "Load a verb tree from a file. Usage: load <file_path> [--json]",
    "list": "List all infinitive verbs in the tree. Usage: list",
    "size": "Display the size of the verb tree. Usage: size",
    "health": "Perform a health check on the verb tree. Usage: health",
    "has": "Check if a verb exists in the tree. Usage: has <verb>",
    "get": "Get conjugation data for a verb. Usage: get <verb>",
    "lookup": "Lookup all conjugated forms for an infinitive verb. Usage: lookup <infinitive> [--mood <mood>] [--tense <tense>] [--pronoun <pronoun>]",
    "extend": "Extend the verb tree with predefined data. Usage: extend",
    "insert": "Insert a new conjugated verb form into the tree. Usage: insert <infinitive> <mood> <tense> <pronoun> <form>",
    "save": "Save the verb tree to a file. Usage: save <file_path> [--json]",
    "autosave": "Set auto-save option. Usage: autosave <true|false>",
}

def get_argparser_for_command(command: str) -> ap.ArgumentParser:
    if hasattr(globals()[f"{command}_argparser"], "parse_args"):
        return globals()[f"{command}_argparser"]
    else:
        raise ValueError(f"No argument parser found for command '{command}'")


def mainloop():
    while True:
        if auto_save:
            color = COLORS["blue"]
        elif edited:
            color = COLORS["yellow"]
        else:
            color = COLORS["green"]
        full_cmd = input(f"{color}{tree_filename.split("/")[-1]}> \033[0m").strip()
        cmd, args = full_cmd.split(" ", 1) if " " in full_cmd else (full_cmd, "")
        args = args.split(" ") if args else []

        if cmd == "exit" or cmd == "quit":
            if edited:
                if auto_save:
                    tree.save(tree_filename)
                    print(f"Changes auto-saved to {tree_filename}.")
                else:
                    confirm = input("You have unsaved changes. Quit without saving? (y/n): ").strip().lower()
                    if confirm != "y":
                        return
            print("Bye.")
            exit(0)
        elif cmd == "help":
            if args and args[0] in HELPS:
                print(HELPS[args[0]])
            else:
                print("Available commands:")
                for command in OPERATIONS.keys():
                    print(f"  - {command}")
                print("Type 'help <command>' for more details on a specific command.")
        elif cmd in OPERATIONS:
            parser = get_argparser_for_command(cmd)
            try:
                parsed_args = parser.parse_args(args)
                OPERATIONS[cmd](**vars(parsed_args))
            except Exception as e:
                print(f"Error executing command '{cmd}': {e.__class__.__name__}: {e}")
        else:
            print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    print("Welcome to the Verb Tree CLI. Type 'help' for a list of commands.")
    mainloop()