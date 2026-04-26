import os
import json
import sys

from gamuLogger import Logger

DIRPATH = os.path.dirname(os.path.abspath(__file__))

Logger.set_module("utils")

class Cache:
    """
    Decorator that cache the results of a function based on its arguments.
    Usage:
    @Cache
    def my_function(args):
        ...
    """
    _cache = {}
    
    def __init__(self, func):
        self.func = func
        
    def __call__(self, *args):
        func_cache = Cache._cache.get(self.func.__name__, {})
        if str(args) in func_cache:
            return func_cache[str(args)]
        Cache._cache[self.func.__name__] = func_cache
        result = self.func(*args)
        func_cache[str(args)] = result
        return result


def get_output_dir(code : str, chapter : int) -> str:
    output_dir = f"output/{code}/{chapter:02d}/"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def save_structure_data(data : list|dict, output_dir : str, type : str):
    output_file = f"{output_dir}{type}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    Logger.info(f"Saved {type} data to {output_file}")
    

def append_to_file(output_path: str, word: str):
    """
    Append content to a file
    Do nothing if word is already in the file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_words = set(line.strip() for line in f)
    else:
        existing_words = set()
        
    if word not in existing_words:
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(word+"\n")
        Logger.debug(f"Appended '{word}' to {output_path}")
        
def save_graphml_file(output_path: str, content: str):
    """
    Save content to a GraphML file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    Logger.info(f"GraphML saved to {output_path}")
        
def resource(filename : str) -> str:
    """
    Get the path to a resource file
    """
    return os.path.join(DIRPATH, "data", filename)