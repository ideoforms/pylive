class LiveException(Exception):
    """
    Base class for all Live-related errors
    """
    pass

class LiveConnectionError(LiveException):
    """
    Error establishing a connection to AbletonOSC.
    """
    pass

class LiveIOError(LiveException):
    """
    Error accessing a file descriptor.
    """
    pass

class LiveInvalidOperationException(LiveException):
    """
    Error performing an operation.
    """
