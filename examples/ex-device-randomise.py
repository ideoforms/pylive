#!/usr/local/bin/python

#------------------------------------------------------------------------
# pylive: ex-device-randomise.py
#
# Once per beat, randomise a parameter of a random device.
#------------------------------------------------------------------------

import live
import random

set = live.Set()

#------------------------------------------------------------------------
# To avoid having to re-scan the set each time we run this example,
# we can cache the set's state which can be reloaded in future.
#
# Try running this example twice on a non-trivial set.
#------------------------------------------------------------------------
try:
	set.load("ex-device-randomise")
except:
	set.scan(scan_devices = True)
	set.save("ex-device-randomise")

set.play()

while True:
	set.wait_for_next_beat()

	#------------------------------------------------------------------------
	# Select a random parameter of a random device
	# (skipping param 0, which is always Device On/Off)
	#------------------------------------------------------------------------
	try:
		track = random.choice(set.tracks)
		device = random.choice(track.devices)
		parameter = random.choice(device.parameters[1:])
		print "track %s, device %s, parameter %s" % (track, device, parameter)

		parameter.randomise()

	except:
		#------------------------------------------------------------------------
		# Might fail if we don't have any tracks, or have a track without
		# devices, etc.
		#------------------------------------------------------------------------
		pass

