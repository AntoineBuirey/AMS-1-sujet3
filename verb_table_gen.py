from google import genai
import re
import json
import tempfile
import os
from typing import TypeVar
from verbs_engine import VerbTree, VerbData, mood_map, tense_map, pronoun_map

client = genai.Client(api_key="AIzaSyCjmmCPI7RjpRRlxwCUEfs8BbZS1mbL8b8")

INFINITIVES_FILE = "missing_verbs.txt"

PROMPT = """
Génère une liste JSON (tableau de tableaux) contenant toutes les conjugaisons françaises du verbe '{verb}'.
Chaque tableau interne doit contenir, dans cet ordre : forme_conjuguée, infinitif, mode, temps, et personne.
Les combinaisons Mode/Temps à inclure sont :
Indicatif (Présent, Imparfait, Passé Simple, Futur Simple, Passé Composé, Plus-que-parfait, Passé Antérieur, Futur Antérieur),
Subjonctif (Présent, Imparfait, Passé, Plus-que-parfait), Conditionnel (Présent, Passé), Impératif (Présent, Passé),
Infinitif (Présent, Passé), et Participe (Présent, Passé).
N'ajoute pas d'autres modes ou temps.
Pour personne, utilise 'je', 'tu', 'il/elle/on', 'nous', 'vous', 'ils/elles', ou 'n/a'.
Inclus les 4 formes du participe passé.
Exemple : [['aime', 'aimer', 'indicatif', 'présent', 'je'], ...].
"""

def generate_table(verb: str) -> list[list[str]]:
    tries = 2
    while tries > 0:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=PROMPT.format(verb=verb))

        if not response.text:
            tries -= 1
            print(f"Empty response when generating conjugation table for verb '{verb}'. Retrying... ({tries} tries left)")
            continue
        result = response.text.replace("```json", "").replace("```", "").strip()

        return json.loads(result)
    raise ValueError(f"Could not generate conjugation table for verb '{verb}' after multiple attempts.")


def validate(data : list[list[str]]) -> tuple [bool, list[str]]:
    # must have 48 forms with the mood 'indicatif'
    
    good = True
    reasons = []
    
    indicatif_count = sum(1 for entry in data if entry[2] == 'indicatif')
    if indicatif_count != 48:
        good = False
        reasons.append(f"Incorrect number of 'indicatif' forms. (got {indicatif_count} instead of 48)")

    # must have 12 forms with 'conditionnel' mood
    conditionnel_count = sum(1 for entry in data if entry[2] == 'conditionnel')
    if conditionnel_count != 12:
        good = False
        reasons.append(f"Incorrect number of 'conditionnel' forms. (got {conditionnel_count} instead of 12)")

    # must have all four past participle forms
    participe_passe_forms = {r"^.*[^s|e|es]$", r"^.*e$", r"^.*s$", r"^.*es$"}
    found_forms = set()
    for entry in data:
        if entry[2] == 'participe' and entry[3] == 'passé':
            for form in participe_passe_forms:
                if re.fullmatch(form, entry[0]):
                    found_forms.add(form)
    if found_forms != participe_passe_forms:
        good = False
        reasons.append(f"Missing some past participle forms. (found {len(found_forms)} out of 4)")

    # must have 24 forms in 'subjonctif' mood
    subjonctif_count = sum(1 for entry in data if entry[2] == 'subjonctif')
    if subjonctif_count != 24:
        good = False
        reasons.append(f"Incorrect number of 'subjonctif' forms. (got {subjonctif_count} instead of 24)")

    # must have 6 'impératif' forms
    imperatif_count = sum(1 for entry in data if entry[2] == 'impératif')
    if imperatif_count != 6:
        good = False
        reasons.append(f"Incorrect number of 'impératif' forms. (got {imperatif_count} instead of 6)")

    # must have 2 'infinitif' forms
    infinitif_count = sum(1 for entry in data if entry[2] == 'infinitif')
    if infinitif_count != 2:
        good = False
        reasons.append(f"Incorrect number of 'infinitif' forms. (got {infinitif_count} instead of 2)")

    # must have 1 'participe présent' form
    participe_present_count = sum(1 for entry in data if entry[2] == 'participe' and entry[3] == 'présent')
    if participe_present_count != 1:
        good = False
        reasons.append(f"Incorrect number of 'participe présent' forms. (got {participe_present_count} instead of 1)")

    return good, reasons


def ask_manual_confirm(data : list[list[str]]) -> bool:
    # create a temporary file to display the data, and ask the user to check it and confirm it's correct
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", dir=".") as tmpfile:
        json.dump(data, tmpfile, ensure_ascii=False, indent=4)
        tmpfile.flush()
        tmpfile_path = tmpfile.name
        print(f"Please review the generated conjugation data in the file: {tmpfile_path}")
        confirm = input("Is the data correct? (y/n): ").strip().lower()
    tmpfile.close()
    return confirm == 'y'


def can_be_added(verb_data: list[list[str]], allow_manual : bool = True) -> bool:
    valid, messages = validate(verb_data)
    if not valid:
        print(f"Auto-validation failed:\n\t- {'\n\t- '.join(messages)}")
        if not allow_manual:
            return False
        if not ask_manual_confirm(verb_data):
            print("User rejected the generated data.")
            return False
        else:
            print("User accepted the generated data.")
    else:
        print("Auto-validation passed.")
    return True


def save_generated(verb: str, data: list[list[str]]):
    filename = f"db_filling_data/{verb}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

T = TypeVar('T', str, tuple, list, dict)
def set_in_lowercase(item : T) -> T:
    if isinstance(item, str):
        return item.lower()
    elif isinstance(item, tuple) or isinstance(item, list):
        return type(item)(set_in_lowercase(i) for i in item)
    elif isinstance(item, dict):
        return {set_in_lowercase(k): set_in_lowercase(v) for k, v in item.items()}
    else:
        return item

def gen_add_verb(verb: str, tree: VerbTree):
    generated_data = generate_table(verb)
    generated_data = set_in_lowercase(generated_data)
    if not can_be_added(generated_data):
        print(f"Skipping verb '{verb}' due to validation failure.")
        save_generated(verb, generated_data)
        print(f"Saved generated data for verb '{verb}' to file for further review.")
        return
    for entry in generated_data:
        form_conjugated, infinitif, mode, temps, personne = entry
        verb_data = VerbData(
            infinitif,
            mood_map[mode],
            tense_map[temps],
            pronoun_map[personne]
        )
        if tree.exist(form_conjugated, verb_data):
            print(f"Form '{form_conjugated}' already exists in the tree. Skipping insertion.")
            continue
        tree.insert(form_conjugated, verb_data)


def remove_from_file(verb: str):
    with open(INFINITIVES_FILE, "r", encoding="utf-8") as f:
        verbs = [line.strip() for line in f if line.strip()]
    verbs = [v for v in verbs if v != verb]
    with open(INFINITIVES_FILE, "w", encoding="utf-8") as f:
        for v in verbs:
            f.write(v + "\n")
    print(f"Removed verb '{verb}' from {INFINITIVES_FILE}.")


def gen_insert(tree_file : str):
    with open(INFINITIVES_FILE, "r", encoding="utf-8") as f:
        verbs = [fline.strip() for fline in f if fline.strip()]
    
    tree = VerbTree.load(tree_file)
    nb_elements_length = len(str(len(verbs)))
    for i, verb in enumerate(verbs):
        print(f"{i+1:0{nb_elements_length}}/{len(verbs):0{nb_elements_length}} - Inserting conjugations for verb '{verb}' into the verb tree.")
        gen_add_verb(verb, tree)
        remove_from_file(verb)
        tree.save(tree_file)
    print(f"Finished inserting verbs into the verb tree '{tree_file}'.")
    print("Inserted verbs:\n", ", ".join(set(verbs)))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and insert verb conjugations into a verb tree.")
    parser.add_argument("--all", action="store_true", help="Process all verbs without skipping any.")
    parser.add_argument("--select", "-s", type=str, nargs="+", help="List of verb infinitives to process. In that mode, ignore the config file.")
    args = parser.parse_args()
    
    if args.all:
        treefile = "verb.data"
        
        if not os.path.exists(treefile):
            tree = VerbTree()
            tree.save(treefile)
            print(f"Created empty verb tree file: {treefile}")
        
        gen_insert(treefile)
    
    elif args.select:
        treefile = "verb.data"
        
        if not os.path.exists(treefile):
            tree = VerbTree()
            tree.save(treefile)
            print(f"Created empty verb tree file: {treefile}")
        
        tree = VerbTree.load(treefile)
        for verb in args.select:
            print(f"Inserting conjugations for verb '{verb}' into the verb tree.")
            gen_add_verb(verb, tree)
        tree.save(treefile)
        print(f"Finished inserting selected verbs into the verb tree '{treefile}'.")
    
    else:
        parser.print_help()