import logging

logger = logging.getLogger("live")

def name_cache(fn):
    """
    Decorator enabling pairs of set_XX/get_XX methods to cache their
    values, to avoid repeatedly querying the Live set for values which we know
    haven't changed.

    If the 'caching' attribute is set of the object containing these 
    methods, the values specifed in 'set' (or initially queried with
    'get') will be stored again for the future.

    This is used so that we can query (say) our Live tempo value once,
    and assume that it will remain the same unless we apply a manual
    set_tempo.

    This will fall out of sync if the value of tempo is externally
    changed!
    """

    name = fn.__name__
    action = name[:3]
    variable = name[4:]

    def cached_fn(obj, *args, **kwargs):
        if hasattr(obj, "caching") and not obj.caching:
            return fn(obj, *args)

        if not hasattr(obj, "__cache"):
            obj.__cache = {}

        if action == "set":
            if "cache_only" not in kwargs:
                fn(obj, *args)
            obj.__cache[variable] = args[0]
        elif action == "get":
            if not variable in obj.__cache:
                obj.__cache[variable] = fn(obj, *args)
            return obj.__cache[variable]

    return cached_fn

