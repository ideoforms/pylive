import time
import signal
import inspect
import threading

import liblo

from .object import LoggingObject
from .exceptions import LiveConnectionError

def singleton(cls):
    instances = {}
    def getinstance(*args):
        if cls not in instances:
            instances[cls] = cls(*args)
        return instances[cls]
    return getinstance

#------------------------------------------------------------------------
# Helper methods to save instantiating an object when making calls.
#------------------------------------------------------------------------

def query(*args, **kwargs):
    return Query().query(*args, **kwargs)

def cmd (*args, **kwargs):
    Query().cmd(*args, **kwargs)

@singleton
class Query(LoggingObject):
    """ Object responsible for passing OSC queries to the LiveOSC server,
    parsing and proxying responses.

    This object is a singleton, under the assumption that only one Live instance
    can be running, so only one global Live Query object should be needed.

    Following this assumption, static helper functions also exist:

        live.query(path, *args)
        live.cmd(path, *args)
    """

    def __init__(self, address=("localhost", 9000), listen_port=9001):
        self.beat_callback = None
        self.startup_callback = None
        self.listen_port = listen_port

        #------------------------------------------------------------------------
        # Handler callbacks for particular messages from Live.
        # Used so that other processes can register callbacks when states change.
        #------------------------------------------------------------------------
        self.handlers = {}

        self.osc_address = address
        self.osc_target = liblo.Address(address[0], address[1])
        self.osc_server = liblo.Server(listen_port)
        self.osc_server.add_method(None, None, self.handler)
        self.osc_server_thread = None
        self.osc_server.add_bundle_handlers(self.start_bundle_handler, self.end_bundle_handler)

        self.osc_read_event = None
        self.osc_timeout = 3.0

        self.osc_server_events = {}

        self.query_address = None
        self.query_rv = []

        self.listen()

    def osc_server_read(self):
        while True:
            self.osc_server.recv(10)

    def listen(self):
        self.osc_server_thread = threading.Thread(target=self.osc_server_read)
        self.osc_server_thread.setDaemon(True)
        self.osc_server_thread.start()

    def stop(self):
        """ Terminate this query object and unbind from OSC listening. """
        pass

    def cmd(self, msg, *args):
        """ Send a Live command without expecting a response back:

            live.cmd("/live/tempo", 110.0) """
        
        self.log_debug("OSC output: %s %s", msg, args)
        try:
            liblo.send(self.osc_target, msg, *args)
        except Exception as e:
            raise LiveConnectionError("Couldn't send message to Live (is LiveOSC present and activated?)")

    def query(self, msg, *args, **kwargs):
        """ Send a Live command and synchronously wait for its response:

            return live.query("/live/tempo")

        Returns a list of values. """

        #------------------------------------------------------------------------
        # Use **kwargs because we want to be able to specify an optional kw
        # arg after variable-length args -- 
        # eg live.query("/set/freq", 440, 1.0, response_address = "/verify/freq")
        #
        # http://stackoverflow.com/questions/5940180/python-default-keyword-arguments-after-variable-length-positional-arguments
        #------------------------------------------------------------------------

        #------------------------------------------------------------------------
        # Some calls produce responses at different addresses
        # (eg /live/device -> /live/deviceall). Specify a response_address to
        # take account of this.
        #------------------------------------------------------------------------
        response_address = kwargs.get("response_address", None)
        if response_address:
            response_address = response_address
        else:
            response_address = msg

        #------------------------------------------------------------------------
        # Create an Event to block the thread until this response has been
        # triggered.
        #------------------------------------------------------------------------
        self.osc_server_events[response_address] = threading.Event()

        #------------------------------------------------------------------------
        # query_rv will be populated by the callback, storing the return value
        # of the OSC query.
        #------------------------------------------------------------------------
        self.query_address = response_address
        self.query_rv = []
        self.cmd(msg, *args)

        #------------------------------------------------------------------------
        # Wait for a response. 
        #------------------------------------------------------------------------
        timeout = kwargs.get("timeout", self.osc_timeout)
        rv = self.osc_server_events[response_address].wait(timeout)

        if not rv:
            raise LiveConnectionError("Timed out waiting for response from LiveOSC. Is Live running and LiveOSC installed?")

        return self.query_rv

    def start_bundle_handler(self, *args):
        self.log_debug("OSC: start bundle")

    def end_bundle_handler(self, *args):
        self.log_debug("OSC: end bundle")

    def handler(self, address, data, types):
        self.log_debug("OSC input: %s %s" % (address, data))

        #------------------------------------------------------------------------
        # Execute any callbacks that have been registered for this message
        #------------------------------------------------------------------------
        if address in self.handlers:
            for handler in self.handlers[address]:
                handler(*data)

        #------------------------------------------------------------------------
        # If this message is awaiting a synchronous return, trigger the
        # thread event and update our return value. 
        #------------------------------------------------------------------------
        if address == self.query_address:
            self.query_rv += data
            self.osc_server_events[address].set()
            return

        if address == "/live/beat":
            if self.beat_callback is not None:
                #------------------------------------------------------------------------
                # Beat callbacks are used if we want to trigger an event on each beat,
                # to synchronise with the timing of the Live set.
                #
                # Callbacks may take one argument: the current beat count.
                # If not specified, call with 0 arguments.
                #------------------------------------------------------------------------
                has_arg = False
                try:
                    signature = inspect.signature(self.beat_callback)
                    has_arg = len(signature.parameters) > 0
                except:
                    # Python 2
                    argspec = inspect.getargspec(self.beat_callback)
                    has_arg = len(argspec.args) > 0 and argspec.args[-1] != "self"

                if has_arg:
                    self.beat_callback(data[0])
                else:
                    self.beat_callback()

        elif address == "/remix/oscserver/startup":
            if self.startup_callback is not None:
                self.startup_callback()

    def add_handler(self, address, handler):
        if not address in self.handlers:
            self.handlers[address] = []
        self.handlers[address].append(handler)

