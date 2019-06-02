class LiveException(Exception):
    """Base class for all Live-related errors
    """
    pass

class LiveConnectionError(LiveException):
    """ Error establishing a connection to LiveOSC. """
    pass

class LiveIOError(LiveException):
    """ Error accessing a file descriptor. """
    pass

class LiveInvalidOperationException(LiveException):
    """ Error performing an operation """
