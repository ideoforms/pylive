import time
import signal
import inspect
import threading

from OSC import *
from live.object import *

class LiveError(Exception):
	"""Base class for all Live-related errors
	"""
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return self.message


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

def query_one(*args, **kwargs):
	return Query().query_one(*args, **kwargs)

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
		live.query_one(path, *args)
		live.cmd(path, *args)
	"""

	def __init__(self, address = ("localhost", 9000), listen_port = 9001):
		self.indent = 0
		self.beat_callback = None
		self.listening = False
		self.listen_port = listen_port

		# handler callbacks for particular messages from Live.
		# used so that other processes can register callbacks when states change.
		self.handlers = {}

		self.osc_address = address
		self.osc_client = OSCClient()
		self.osc_client.connect(address)
		self.osc_server = OSCServer(("localhost", self.listen_port))
		self.osc_server_thread = None
		self.osc_read_event = None
		self.osc_timeout = 5

		self.response_address = None

		self.listen()

	def __str__(self):
		return "live.query"

	def stop(self):
		""" Terminate this query object and unbind from OSC listening. """
		if self.listening:
			self.osc_server.close()
			self.listening = False

	def listen(self):
		""" Commence listening for OSC messages from LiveOSC. """
		try:
			self.trace("started listening")
			self.osc_server.addMsgHandler("default", self.handler)
			self.osc_server_thread = threading.Thread(target = self.osc_server.serve_forever)
			self.osc_server_thread.setDaemon(True)
			self.osc_server_thread.start()
			self.listening = True
		except Exception, e:
			self.warn("listen failed (couldn't bind to port %d): %s" % (self.listen_port, e))

	def cmd(self, msg, *args):
		""" Send a Live command without expecting a response back:

			live.cmd("/live/tempo", 110.0) """
		
		msg = OSCMessage(msg)
		msg.extend(list(args))
		try:
			self.osc_client.send(msg)
		except OSCClientError:
			raise LiveError("Couldn't send message to Live (is LiveOSC present and activated?)")

	def query(self, msg, *args, **kwargs):
		""" Send a Live command and synchronously wait for its response:

			return live.query("/live/tempo")

		Returns a list of values. """

		#------------------------------------------------------------------------
		# use **kwargs because we want to be able to specify an optional kw
		# arg after variable-length args -- 
		# eg live.query("/set/freq", 440, 1.0, response_address = "/verify/freq")
		# http://stackoverflow.com/questions/5940180/python-default-keyword-arguments-after-variable-length-positional-arguments
		#------------------------------------------------------------------------
		if not self.listening:
			self.listen()

		#------------------------------------------------------------------------
		# some calls produce responses at different addresses
		# (eg /live/device -> /live/deviceall). specify a response_address to
		# take account of this.
		#------------------------------------------------------------------------
		response_address = kwargs.get("response_address", None)
		if response_address:
			self.response_address = response_address
		else:
			self.response_address = msg

		self.query_rv = []

		self.osc_server_event = threading.Event()

		msg = OSCMessage(msg)
		msg.extend(list(args))
		try:
			self.osc_client.send(msg)
		except OSCClientError:
			raise LiveError("Couldn't send message to Live (is LiveOSC present and activated?)")

		rv = self.osc_server_event.wait(self.osc_timeout)
		if not rv:
			print "*** timed out waiting for server response"

		return self.query_rv

	def query_one(self, msg, *args):
		""" Send a Live command and synchronously wait for its response:

			return live.query_one("/live/tempo")

		Returns a single scalar value (in this case, a float). """
		rv = self.query(msg, *args)
		if not rv:
			return None
		return rv[0]

	def handler(self, address, tags, data, source):
		# print "handler: %s %s" % (address, data)
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
		if address == self.response_address:
			self.query_rv += data
			self.osc_server_event.set()
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
				# It might be nice to send the current beat # as a parameter, but we
				# also want to be able to handle callbacks with no args -- TODO: look
				# into this.
				#------------------------------------------------------------------------
				# argspec = inspect.getargspec(self.beat_callback)
				# if len(argspec.args) > 0:
				#	self.beat_callback(data[0])
				#------------------------------------------------------------------------
				self.beat_callback()

	def add_handler(self, address, handler):
		if not address in self.handlers:
			self.handlers[address] = []
		self.handlers[address].append(handler)

