from enum import Enum
from typing import Any
from random import choice
from string import ascii_lowercase, digits
import json


class NodeType(Enum):
    VERB = 1
    LETTER = 2


class Mood(Enum):
    INDICATIF = 1
    SUBJONCTIF = 2
    IMPERATIF = 3
    CONDITIONNEL = 4
    INFINITIF = 5
    PARTICIPE = 6
    
class Tense(Enum):
    PRESENT = 1
    IMPARFAIT = 2
    FUTUR_SIMPLE = 3
    PASSE_SIMPLE = 4
    PASSE_COMPOSE = 5
    PASSE = 6
    PLUS_QUE_PARFAIT = 7
    FUTUR_ANTERIEUR = 8
    PASSE_ANTERIEUR = 9

class Pronoun(Enum):
    JE = 1
    TU = 2
    IL_ELLE_ON = 3
    NOUS = 4
    VOUS = 5
    ILS_ELLES = 6
    NA = 7
    MASCULIN_SINGULIER = 8
    FEMININ_SINGULIER = 9
    MASCULIN_PLURIEL = 10
    FEMININ_PLURIEL = 11
    
    

tense_map = {
    "présent": Tense.PRESENT,
    "imparfait": Tense.IMPARFAIT,
    "futur simple": Tense.FUTUR_SIMPLE,
    "passé simple": Tense.PASSE_SIMPLE,
    "passé composé": Tense.PASSE_COMPOSE,
    "passé": Tense.PASSE,
    "plus-que-parfait": Tense.PLUS_QUE_PARFAIT,
    "futur antérieur": Tense.FUTUR_ANTERIEUR,
    "passé antérieur": Tense.PASSE_ANTERIEUR,
}
mood_map = {
    "indicatif": Mood.INDICATIF,
    "subjonctif": Mood.SUBJONCTIF,
    "impératif": Mood.IMPERATIF,
    "conditionnel": Mood.CONDITIONNEL,
    "infinitif": Mood.INFINITIF,
    "participe": Mood.PARTICIPE,
}
pronoun_map = {
    "je": Pronoun.JE,
    "tu": Pronoun.TU,
    "il/elle/on": Pronoun.IL_ELLE_ON,
    "nous": Pronoun.NOUS,
    "vous": Pronoun.VOUS,
    "ils/elles": Pronoun.ILS_ELLES,
    "n/a": Pronoun.NA,
    "masculin singulier": Pronoun.MASCULIN_SINGULIER,
    "féminin singulier": Pronoun.FEMININ_SINGULIER,
    "masculin pluriel": Pronoun.MASCULIN_PLURIEL,
    "féminin pluriel": Pronoun.FEMININ_PLURIEL,
}    

tense_map_inv = {v: k for k, v in tense_map.items()}
mood_map_inv = {v: k for k, v in mood_map.items()}
pronoun_map_inv = {v: k for k, v in pronoun_map.items()}
    
    
def gen_id(length: int = 8) -> str:
    characters = ascii_lowercase + digits
    return ''.join(choice(characters) for _ in range(length))

    
class VerbData:
    def __init__(self, infinitive: str, mood: Mood, tense: Tense, pronoun: Pronoun):
        self.infinitive = infinitive
        self.mood = mood
        self.tense = tense
        self.pronoun = pronoun

    def __str__(self):
        return f"{tense_map_inv[self.tense]} {mood_map_inv[self.mood]} {pronoun_map_inv[self.pronoun]} - {self.infinitive}"
    
    def to_string(self):
        return f"{self.infinitive},{self.mood.value},{self.tense.value},{self.pronoun.value}"
    
    @classmethod
    def from_string(cls, data: str) -> 'VerbData':
        parts = data.split(',')
        infinitive = parts[0]
        mood = Mood(int(parts[1]))
        tense = Tense(int(parts[2]))
        pronoun = Pronoun(int(parts[3]))
        return cls(infinitive, mood, tense, pronoun)

class Node:
    def __init__(self, value : Any):
        self.value = value
        self.children : dict[str, 'Node'] = {}
        
    def identifier(self) -> str:
        return str(self.value)
        
    def add_child(self, child_node : 'Node'):
        self.children[child_node.identifier()] = child_node
    
    def get_child(self, value : str) -> 'Node | None':
        return self.children.get(value, None)
    
    def __next__(self):
        for child in self.children.values():
            yield child
    
    def has_child(self, value : str) -> bool:
        return value in self.children
    
    def __repr__(self):
        return f"Node(value={self.value}, children={list(self.children.keys())})"
    
    def __str__(self):
        return f"{self.value}"
    
    def show(self, level=0) -> str:
        indent = "  " * level
        result = f"{indent}{self.value}\n"
        for child in self.children.values():
            result += child.show(level + 1)
        return result
            
    def size(self) -> int:
        total_size = 1  # Count this node
        for child in self.children.values():
            total_size += child.size()
        return total_size

    def is_verb(self) -> bool:
        raise NotImplementedError("is_verb method should be implemented in subclasses.")
    
    def save(self) -> dict:
        children_data = {key: child.save() for key, child in self.children.items()}
        return {
            "v": self.serialize(),
            "c": children_data
        }
    
    @classmethod
    def load(cls, data: dict) -> 'Node':
        value = data["v"]
        if ',' in value:  # Simple check to differentiate VerbNode from LetterNode
            node = VerbNode.deserialize(value)
        else:
            node = LetterNode.deserialize(value)
        for key, child_data in data["c"].items():
            child_node = Node.load(child_data)
            node.add_child(child_node)
        return node
        
    def serialize(self) -> str:
        raise NotImplementedError("serialize method should be implemented in subclasses.")
    
    @classmethod
    def deserialize(cls, data: str) -> 'Node':
        raise NotImplementedError("deserialize method should be implemented in subclasses.")


class LetterNode(Node):
    def __init__(self, value : str):
        super().__init__(value)

    def is_verb(self) -> bool:
        return False
    
    def serialize(self) -> str:
        return self.value
    
    @classmethod
    def deserialize(cls, data: str) -> 'LetterNode':
        return cls(data)
    
    
class VerbNode(Node):
    def __init__(self, value : VerbData):
        super().__init__(value)
        self.id = str(gen_id())
        
    def identifier(self) -> str:
        return self.id

    def is_verb(self) -> bool:
        return True

    def serialize(self) -> str:
        return self.value.to_string()
    
    @classmethod
    def deserialize(cls, data: str) -> 'VerbNode':
        verb_data = VerbData.from_string(data)
        return cls(verb_data)


class VerbTree:
    def __init__(self):
        self.root = LetterNode("")
    
    def insert(self, verb : str, data : VerbData):
        current_node = self.root
        for char in verb:
            if current_node is None:
                raise Exception("Current node is None while inserting verb.")
            if not current_node.has_child(char):
                new_node = LetterNode(char)
                current_node.add_child(new_node)
            current_node = current_node.get_child(char)  # type: ignore
        # Mark the end of the verb
        if current_node is None:
            raise Exception("Current node is None while inserting verb at the end.")
        verb_node = VerbNode(data)
        current_node.add_child(verb_node)
    
    def search(self, verb : str) -> bool:
        current_node = self.root
        for char in verb:
            if current_node is None:
                return False
            current_node = current_node.get_child(char)
        if current_node is None:
            return False
        # Check if there's a verb node among the children
        for child in current_node.children.values():
            if child.is_verb():
                return True
        return False
    
    def get(self, verb : str) -> list[VerbData]:
        current_node = self.root
        for char in verb:
            if current_node is None:
                return []
            current_node = current_node.get_child(char)
        if current_node is None:
            return []
        # Collect all verb data from verb nodes among the children
        verb_data_list = []
        for child in current_node.children.values():
            if child.is_verb():
                verb_data_list.append(child.value)  # type: ignore
        return verb_data_list
    
    def save(self, filepath : str) -> None:
        data = self.root.save()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    
    @classmethod
    def load(cls, filepath : str) -> 'VerbTree':
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        tree = cls()
        tree.root = Node.load(data)
        return tree
    
    def save_flat(self, filepath : str) -> None:
        verbs = []

        def traverse(node: Node, current_verb: str):
            if node.is_verb():
                verb_data: VerbData = node.value  # type: ignore
                verbs.append((
                    current_verb,
                    verb_data.infinitive,
                    verb_data.mood.value,
                    verb_data.tense.value,
                    verb_data.pronoun.value,
                ))
            for child in node.children.values():
                if isinstance(child, LetterNode):
                    traverse(child, current_verb + child.value)
                elif isinstance(child, VerbNode):
                    traverse(child, current_verb)
        traverse(self.root, "")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(verbs, f, ensure_ascii=False, separators=(',', ':'))
            
    @classmethod
    def load_flat(cls, filepath : str) -> 'VerbTree':
        with open(filepath, "r", encoding="utf-8") as f:
            verbs = json.load(f)
        tree = cls()
        for conjugated_form, infinitive, mood, tense, pronoun in verbs:
            mood = Mood(mood)
            tense = Tense(tense)
            pronoun = Pronoun(pronoun)
            verb_data = VerbData(infinitive, mood, tense, pronoun)
            tree.insert(conjugated_form, verb_data)
        return tree
    
    def get_verb_number(self) -> int:
        def count_verbs(node: Node) -> int:
            count = 0
            if node.is_verb():
                count += 1
            for child in node.children.values():
                count += count_verbs(child)
            return count
        return count_verbs(self.root)
    
    def __len__(self) -> int:
        def count_nodes(node: Node) -> int:
            count = 1  # Count this node
            for child in node.children.values():
                count += count_nodes(child)
            return count
        return count_nodes(self.root)
    
    
    def list_verbs(self) -> list[str]:
        """
        Extract all infinitive verbs from the VerbTree.
        """
        verbs = set()

        def traverse(node: Node):
            if node.is_verb():
                verbs.add(node.value.infinitive)  # type: ignore
            for child in node.children.values():
                traverse(child)

        traverse(self.root)
        return list(verbs)


if __name__ == "__main__":
    import argparse
    import time
    
    argparser = argparse.ArgumentParser(description="Verb Tree Operations")
    argparser.add_argument("--list", action="store_true", help="List all infinitive verbs in the tree")
    argparser.add_argument("--has", type=str, help="Check if a verb exists in the tree", action="store")
    argparser.add_argument("--get", type=str, help="Get conjugation data for a verb", action="store")
    argparser.add_argument("--extend", action="store_true", help="Extend the verb tree from verb_data.py")
    argparser.add_argument("--save", type=str, help="Save the verb tree to a specified file", action="store")
    argparser.add_argument("--save-flat", type=str, help="Save the verb tree in flat format to a specified file", action="store")
    argparser.add_argument("--load", type=str, help="Load the verb tree from a specified file", action="store")
    argparser.add_argument("--load-flat", type=str, help="Load the verb tree in flat format from a specified file", action="store")
    args = argparser.parse_args()
    
    if not (args.list or args.has or args.extend or args.get or args.save or args.save_flat, args.load or args.load_flat):
        argparser.print_help()
        
    tree = VerbTree()
        
    if args.load:
        timer = time.time()
        tree = VerbTree.load(args.load)
        print(f"Verb tree loaded from {args.load} in {time.time() - timer:.6f} seconds")
        
    if args.load_flat:
        timer = time.time()
        tree = VerbTree.load_flat(args.load_flat)
        print(f"Verb tree loaded in flat format from {args.load_flat} in {time.time() - timer:.6f} seconds")
    
    if not (args.load or args.load_flat):    
        tree = VerbTree.load_flat("verb.data.json")
    
    if args.list:
        print(tree.list_verbs())
        
    if args.has:
        verb_to_check = args.has
        exists = tree.search(verb_to_check)
        if exists:
            print(f"The verb '{verb_to_check}' exists in the tree.")
        else:
            print(f"The verb '{verb_to_check}' does NOT exist in the tree.")
        
    if args.get:
        verb_to_get = args.get
        conjugations = tree.get(verb_to_get)
        if conjugations:
            print(f"Conjugation data for '{verb_to_get}':")
            for conjugation in conjugations:
                print(f"  {conjugation}")
        else:
            print(f"No conjugation data found for '{verb_to_get}'.")
    
    if args.extend:
        from verb_data import DATA
        for verb in DATA:
            tree.insert(verb[0], VerbData(verb[1], mood_map[verb[2]], tense_map[verb[3]], pronoun_map[verb[4]]))
        
        infinitive = set()
        for verb in DATA:
            infinitive.add(verb[1])
        print(f"inserted {len(DATA)} items from verb_data.py\nverbs added:\n\t{"\n\t".join(sorted(infinitive))}")
        tree.save("verb_tree.json")
        
    if args.save:
        timer = time.time()
        tree.save(args.save)
        print(f"Verb tree saved to {args.save} in {time.time() - timer:.6f} seconds")
        
    if args.save_flat:
        timer = time.time()
        tree.save_flat(args.save_flat)
        print(f"Verb tree saved in flat format to {args.save_flat} in {time.time() - timer:.6f} seconds")
