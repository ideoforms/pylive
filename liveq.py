import time
import signal
import thread

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
class LiveQuery(LoggingObject):
	def __init__(self):
		self.indent = 0
		self.tick_callback = None
		self.listening = False

		self.osc_client = OSCClient()
		self.osc_client.connect(("localhost", 9000))
		self.osc_server = OSCServer(("localhost", 9001))
		self.osc_server_thread = None

	def __str__(self):
		return "live.liveq"

	def stop(self):
		if self.listening:
			self.nolisten()

	def listen(self):
		try:
			self.trace("started listening")
			self.osc_server.addMsgHandler("default", self.handler)
			thread.start_new_thread(self.osc_server.serve_forever, ())
			self.listening = True
		except Exception, e:
			self.warn("listen failed (couldn't bind to port %d): %s" % (self.port, e))

	def nolisten(self):
		print "stopping listening"
		self.osc_server.close()
		self.listening = False

	def clipinfo(self, msg, source = None):
		track = msg[2]
		clips = msg[4:]
		for n in range(0, len(clips), 3):
			number = n / 3
			state = clips[n + 1]
			length = clips[n + 2]
			if state > 0:
				print "clip [%d, %d] %d, %d" % (track, number, state, length)

	def cmd(self, msg, *args):
		# send msg without expected response
		self.osc_client.send(OSCMessage(msg, list(args)))

	def query(self, msg, *args):
		# cheeky way of doing synchronous communication
		# - wait around for response from the OSC thread
		if not self.listening:
			self.listen()

		self.query_address = msg
		self.query_rv = None

		self.osc_client.send(OSCMessage(msg, list(args)))

		# set a timeout just in case things have gone screwy
		# XXX: can't use signals in non-main threads :-(
		# signal.signal(signal.SIGALRM, self.exc)
		# signal.alarm(1)

		counter = 0
		counter_max = 500
		while self.query_rv is None and counter < counter_max:
			# print "...sleep... (%d)" % counter
			time.sleep(0.01)
			counter += 1
		if counter >= counter_max:
			print "timed out waiting for Live response!"

		# signal.alarm(0)

		return self.query_rv

	def query_one(self, msg, *args):
		rv = self.query(msg, *args)
		if rv is None:
			return rv
		return rv[0]

	def handler(self, address, tags, data, source):
		# print "%s: %s" % (address, value)
		if address == self.query_address:
			self.query_rv = data

		if address == "/live/clip/info" and data == [ 0, 0, 3 ]:
			print "TICK"
			if self.tick_callback is not None:
				self.tick_callback()

