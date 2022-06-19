import time
import inspect
import logging
import argparse
import threading

from live.object import LoggingObject
from live.exceptions import LiveConnectionError

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

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

def cmd(*args, **kwargs):
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

    def __init__(self, address=("localhost", 11000), listen_port=11001):
        self.beat_callback = None
        self.startup_callback = None
        self.listen_port = listen_port

        #------------------------------------------------------------------------
        # Handler callbacks for particular messages from Live.
        # Used so that other processes can register callbacks when states change.
        #------------------------------------------------------------------------
        self.handlers = {}

        self.osc_address = address
        self.osc_client = SimpleUDPClient(*address)

        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.pythonosc_handler_wrapper)

        # TODO TODO may need to take more care that this, or the other
        # pythonosc objects, actually close all of their connections before
        # exit / atexit
        # for some reason, maybe most likely something else, there seem to
        # be less frequent apparent "connection" issues with liblo than with
        # pythonosc...
        self.osc_server = ThreadingOSCUDPServer((address[0], listen_port),
                                                self.dispatcher)

        self.osc_server_thread = None
        self.osc_read_event = None
        self.osc_timeout = 3.0
        self.osc_server_events = {}

        self.query_address = None
        self.query_rv = []

        self.listen()

    def listen(self):
        target = self.osc_server.serve_forever

        self.osc_server_thread = threading.Thread(target=target)
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
            self.osc_client.send_message(msg, args)

        # TODO TODO need to modify pythonosc client call / handling so it will
        # also raise an error in this case? (probably)
        except Exception as e:
            self.log_debug(f"During cmd({msg}, {args})")
            raise LiveConnectionError("Couldn't send message to Live (is LiveOSC present and activated?)")

    # TODO maybe compute something like the average latency for a response to
    # arrive for a query (maybe weighted by recency) for debugging whether the
    # timeout is reasonable?
    # TODO + number of commands already processed / sent maybe + maybe log
    # whether particular commands always fail?

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
            self.log_debug(f"Timeout during query({msg}, {args}, {kwargs})")
            # TODO could change error message to not question whether LiveOSC
            # is setup correctly if there has been any successful communication
            # so far...
            raise LiveConnectionError("Timed out waiting for response to query: %s %s. Is Live running and LiveOSC installed?" % (self.query_address, args))

        return self.query_rv

    def pythonosc_handler_wrapper(self, address, *args):
        # TODO may need to unwrap len(args) == 0 case or something like that
        self.handler(address, args, None)

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

        if address == "/live/song/beat":
            if self.beat_callback is not None:
                #------------------------------------------------------------------------
                # Beat callbacks are used if we want to trigger an event on each beat,
                # to synchronise with the timing of the Live set.
                #
                # Callbacks may take one argument: the current beat count.
                # If not specified, call with 0 arguments.
                #------------------------------------------------------------------------
                signature = inspect.signature(self.beat_callback)
                has_arg = len(signature.parameters) > 0

                if has_arg:
                    self.beat_callback(data[0])
                else:
                    self.beat_callback()

        elif address == "/live/startup":
            if self.startup_callback is not None:
                self.startup_callback()

    def add_handler(self, address, handler):
        if not address in self.handlers:
            self.handlers[address] = []
        self.handlers[address].append(handler)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--reload", action="store_true", help="Prompt AbletonOSC to reload code")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    query = Query()
    if args.reload:
        query.cmd("/live/reload")
    print("Awaiting Live events...")
    while True:
        time.sleep(0.1)