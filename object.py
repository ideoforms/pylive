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
		print "created logger: %s" % __name__

	def trace(self, msg = ""):
		print "%s[%s] %s" % (" " * 3 * self.indent, self, msg)

	def warn(self, msg = ""):
		print "[%s] !!! warning: %s !!!" % (self, msg)

	def debug(self, msg = ""):
		if self.debug:
			print "[%s] !!! debug: %s !!!" % (self, msg)
