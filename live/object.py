import live

import logging
logger = logging.getLogger("live")

class LoggingObject(object):
    """ Helper superclass for objects which wish to generate debugging output
    with hierachical indentation.

    Three levels of output are available:

    object.trace()
    object.warn()
    object.debug() """

    def __init__(self):
        self.indent = 0
        self.log_level = 0

        self.logger = logging.getLogger(__name__)
        print("created logger: %s" % __name__)

    def log_info(self, msg = "", *args):
        if msg:
            msg = msg % args
        logger.info("[%s] %s", self, msg)

    def log_warn(self, msg = "", *args):
        msg = msg % args
        logger.warn("[%s] %s", self, msg)

    def log_debug(self, msg = "", *args):
        msg = msg % args
        logger.debug("[%s] %s", self, msg)

def name_cache(fn):
    """ Decorator enabling pairs of set_XX/get_XX methods to cache their
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

