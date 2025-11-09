import os
import json

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
    print(f"[INFO] Saved {type} data to {output_file}")