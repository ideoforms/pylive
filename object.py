class LoggingObject(object):
	def __init__(self):
		self.indent = 0
		self.debug = 0

		try:
			import settings
			self.debug = settings.debu
		except:
			pass

	def debug(self, msg = ""):
		if self.debug:
			print "[%s] !!! debug: %s !!!" % (self, msg)

	def trace(self, msg = ""):
		print "%s[%s] %s" % (" " * 3 * self.indent, self, msg)

	def warn(self, msg = ""):
		print "[%s] !!! warning: %s !!!" % (self, msg)
