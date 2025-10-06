
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


class DebugFunc:
    """
    Decorator that prints the function name, its arguments, and its return value when called.
    In order to enable/disable debug mode, set DebugFunc._debug = True/False
    Usage:
    @DebugFunc
    def my_function(args):
        ...
    """
    _debug = False
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        if not DebugFunc._debug:
            return self.func(*args, **kwargs)
        result = self.func(*args, **kwargs)
        print(f"Function {self.func.__name__} called with args: {args}, kwargs: {kwargs}. Result: {result}")
        return result