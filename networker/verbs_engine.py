from enum import Enum
from typing import Any, IO
from random import choice
from string import ascii_lowercase, digits
import json
import zipfile

from gamuLogger import Logger
Logger.set_module("verbs engine")


def get_char_variants(char: str) -> list[str]:
    """
    Return a list of character variants for the given character.
    """
    variants = {
        'a': ['a', 'à', 'â', 'ä'],
        'c': ['c', 'ç'],
        'e': ['e', 'é', 'è', 'ê', 'ë'],
        'i': ['i', 'î', 'ï'],
        'o': ['o', 'ô', 'ö'],
        'u': ['u', 'ù', 'û', 'ü']
    }
    return variants.get(char, [char])


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
    
    def serialize(self):
        return f"{self.infinitive},{self.mood.value},{self.tense.value},{self.pronoun.value}"
    
    def serialize_binary(self) -> bytes:
        """
        Return a binary representation of the VerbData as follow:
        "infinitive\x1emood\x1etense\x1epronoun"
        """
        return f"{self.infinitive}\x1e{self.mood.value}\x1e{self.tense.value}\x1e{self.pronoun.value}".encode("utf-8")
    
    @classmethod
    def deserialize(cls, data: str) -> 'VerbData':
        parts = data.split(',')
        infinitive = parts[0]
        mood = Mood(int(parts[1]))
        tense = Tense(int(parts[2]))
        pronoun = Pronoun(int(parts[3]))
        return cls(infinitive, mood, tense, pronoun)
    
    @classmethod
    def deserialize_binary(cls, data: bytes) -> 'VerbData':
        parts = data.decode("utf-8").split('\x1e')
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
        
        
    def serialize(self) -> str:
        raise NotImplementedError("serialize method should be implemented in subclasses.")
    
    def serialize_binary(self) -> bytes:
        raise NotImplementedError("serialize_binary method should be implemented in subclasses.")
    
    @classmethod
    def deserialize(cls, data: str) -> 'Node':
        raise NotImplementedError("deserialize method should be implemented in subclasses.")
    
    @classmethod
    def deserialize_binary(cls, data: bytes) -> 'Node':
        raise NotImplementedError("deserialize_binary method should be implemented in subclasses.")

class LetterNode(Node):
    def __init__(self, value : str):
        super().__init__(value)

    def is_verb(self) -> bool:
        return False
    
    def serialize(self) -> str:
        return self.value

    def serialize_binary(self) -> bytes:
        return self.value.encode("utf-8")
    
    @classmethod
    def deserialize(cls, data: str) -> 'LetterNode':
        return cls(data)
    
    @classmethod
    def deserialize_binary(cls, data: bytes) -> 'LetterNode':
        return cls(data.decode("utf-8"))

class VerbNode(Node):
    def __init__(self, value : VerbData):
        super().__init__(value)
        self.id = str(gen_id())
        
    def identifier(self) -> str:
        return self.id

    def is_verb(self) -> bool:
        return True

    def serialize(self) -> str:
        return self.value.serialize()
    
    def serialize_binary(self) -> bytes:
        return self.value.serialize_binary()   
    
    @classmethod
    def deserialize(cls, data: str) -> 'VerbNode':
        verb_data = VerbData.deserialize(data)
        return cls(verb_data)
    
    @classmethod
    def deserialize_binary(cls, data: bytes) -> 'VerbNode':
        verb_data = VerbData.deserialize_binary(data)
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
    
    def exist(self, conjugated_form : str, verb_data : VerbData) -> bool:
        current_node = self.root
        for char in conjugated_form:
            if current_node is None:
                return False
            current_node = current_node.get_child(char)
        if current_node is None:
            return False
        # Check if there's a verb node with the same data among the children
        for child in current_node.children.values():
            if child.is_verb() and \
                child.value.infinitive == verb_data.infinitive and \
                child.value.mood == verb_data.mood and \
                child.value.tense == verb_data.tense and \
                child.value.pronoun == verb_data.pronoun:
                return True
        return False
    
    def __iter__(self):
        """Iterate over all verb nodes in the tree. Yields tuples of (conjugated_form, VerbData)."""
        def traverse(node: Node, current_verb: str):
            if node.is_verb():
                verb_data: VerbData = node.value  # type: ignore
                yield (current_verb, verb_data)
            for child in node.children.values():
                if isinstance(child, LetterNode):
                    yield from traverse(child, current_verb + child.value)
                elif isinstance(child, VerbNode):
                    yield from traverse(child, current_verb)
        yield from traverse(self.root, "")
    
    def get(self, verb : str, strict : bool = True) -> list[VerbData]:
        if strict:
            return self.__get_strict(verb)
        else:
            return self.__get_permissive(verb)
        
        
    def __get_strict(self, verb : str) -> list[VerbData]:
        current_node = self.root
        for char in verb:
            if current_node is None:
                return []
            current_node = current_node.get_child(char)
            Logger.trace(f"Traversing char '{char}': current_node = {current_node}")
        if current_node is None:
            return []
        # Collect all verb data from verb nodes among the children
        verb_data_list = []
        for child in current_node.children.values():
            if child.is_verb():
                verb_data_list.append(child.value)  # type: ignore
        return verb_data_list
    
    def __get_permissive(self, verb : str) -> list[VerbData]:
        # To be implemented
        paths : list[str] = ['']
        for char in verb:
            new_paths : list[str] = []
            char_variants = get_char_variants(char)
            for path in paths:
                current_node = self.root
                for c in path:
                    if current_node is None:
                        break
                    current_node = current_node.get_child(c)
                if current_node is None:
                    continue
                for variant in char_variants:
                    if current_node.has_child(variant):
                        new_paths.append(path + variant)
            paths = new_paths
            Logger.trace(f"After processing char '{char}': possible paths = {paths}")
        # Now collect verb data from all valid paths
        verb_data_list : list[VerbData] = []
        for path in paths:
            current_node = self.root
            for char in path:
                if current_node is None:
                    break
                current_node = current_node.get_child(char)
            if current_node is None:
                continue
            for child in current_node.children.values():
                if child.is_verb():
                    verb_data_list.append(child.value)  # type: ignore
        return verb_data_list
    
    def __save_to_file(self, file : IO) -> None:
        for conjugated_form, verb_data in self:
            line = f"{conjugated_form}\x1d".encode("utf-8") + verb_data.serialize_binary() + b"\n"
            file.write(line)
            
    def save(self, filepath : str) -> None:
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            with zipf.open("data", 'w') as f:
                self.__save_to_file(f)
    
    def save_uncompressed(self, filepath : str) -> None:
        with open(filepath, 'wb') as f:
            self.__save_to_file(f)

    @classmethod
    def __load_from_file(cls, file : IO) -> 'VerbTree':
        tree = cls()
        for line in file:
            line = line.rstrip(b"\n")
            conjugated_form, verb_data_bin = line.split(b"\x1d", 1)
            conjugated_form_str = conjugated_form.decode("utf-8")
            verb_data = VerbData.deserialize_binary(verb_data_bin)
            tree.insert(conjugated_form_str, verb_data)
        return tree

    @classmethod
    def load(cls, filepath : str) -> 'VerbTree':
        tree = cls()
        with zipfile.ZipFile(filepath, 'r') as zipf:
            with zipf.open("data", 'r') as f:
                tree = cls.__load_from_file(f)
        return tree
    
    @classmethod
    def load_uncompressed(cls, filepath : str) -> 'VerbTree':
        tree = cls()
        with open(filepath, 'rb') as f:
            tree = cls.__load_from_file(f)
        return tree
        
    def save_json(self, filepath : str) -> None:
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
    def load_json(cls, filepath : str) -> 'VerbTree':
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

