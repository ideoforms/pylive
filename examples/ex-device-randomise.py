#!/usr/bin/env python

#------------------------------------------------------------------------
# pylive: ex-device-randomise.py
#
# Once per beat, randomise a parameter of a random device.
#------------------------------------------------------------------------
import live
import random
import logging

logging.basicConfig(format="%(asctime)-15s %(message)s")
logging.getLogger("live").setLevel(logging.INFO)

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

tracks_with_devices = list(filter(lambda track: len(track.devices), set.tracks))
if len(tracks_with_devices) == 0:
	raise LiveException("Please open a Live set with at least one device")

set.play()

while True:
	set.wait_for_next_beat()

	#------------------------------------------------------------------------
	# Select a random parameter of a random device
	# (skipping param 0, which is always Device On/Off)
	#------------------------------------------------------------------------
	track = random.choice(tracks_with_devices)
	device = random.choice(track.devices)
	parameter = random.choice(device.parameters[1:])
	print("Track %s, device %s, parameter %s" % (track, device, parameter))

	parameter.randomise()
