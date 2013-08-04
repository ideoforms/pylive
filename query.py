import time
import signal
import threading

from OSC import *
from live.object import *

def singleton(cls):
	instances = {}
	def getinstance(*args):
		if cls not in instances:
			instances[cls] = cls(*args)
		return instances[cls]
	return getinstance

@singleton
class Query(LoggingObject):
	def __init__(self):
		self.indent = 0
		self.tick_callback = None
		self.listening = False
		self.listen_port = 9001

		self.osc_client = OSCClient()
		self.osc_client.connect(("localhost", 9000))
		self.osc_server = OSCServer(("localhost", self.listen_port))
		self.osc_server_thread = None
		self.osc_read_event = None

	def __str__(self):
		return "live.query"

	def stop(self):
		if self.listening:
			self.osc_server.close()
			self.listening = False

	def listen(self):
		try:
			self.trace("started listening")
			self.osc_server.addMsgHandler("default", self.handler)
			self.osc_server_thread = threading.Thread(target = self.osc_server.serve_forever)
			self.osc_server_thread.daemonMode = True
			self.osc_server_thread.start()
			self.listening = True
		except Exception, e:
			self.warn("listen failed (couldn't bind to port %d): %s" % (self.listen_port, e))

	def cmd(self, msg, *args):
		# send msg without expected response
		msg = OSCMessage(msg)
		msg.extend(list(args))
		self.osc_client.send(msg)

	def query(self, msg, *args):
		# cheeky way of doing synchronous communication
		# - wait around for response from the OSC thread
		if not self.listening:
			self.listen()

		self.query_address = msg
		self.query_rv = []

		self.osc_server_event = threading.Event()

		msg = OSCMessage(msg)
		msg.extend(list(args))
		self.osc_client.send(msg)

		rv = self.osc_server_event.wait(5)
		if not rv:
			print "*** timed out waiting for server response"

		return self.query_rv

	def query_one(self, msg, *args):
		rv = self.query(msg, *args)
		if not rv:
			return None
		return rv[0]

	def handler(self, address, tags, data, source):
		if address == self.query_address:
			self.query_rv += data
			self.osc_server_event.set()

		if address == "/live/clip/info" and data == [ 0, 0, 3 ]:
			print "TICK"
			if self.tick_callback is not None:
				self.tick_callback()

