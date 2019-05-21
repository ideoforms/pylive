#!/usr/local/bin/python

#------------------------------------------------------------------------
# pylive: ex-live-scan.py
#
# Demonstrates scanning the live set and outputs its structure.
#------------------------------------------------------------------------

from live import *

import logging

logging.basicConfig(format="%(asctime)-15s %(message)s")
logging.getLogger("live").setLevel(logging.INFO)

#------------------------------------------------------------------------
# Scanning a set with clip names and devices gives a more comprehensive
# overview of the set, but takes significantly longer.
#------------------------------------------------------------------------
set = Set()
set.scan(scan_clip_names = False, scan_devices = True)

for track in set.tracks:
	if track.is_group:
		print(str(track))
	else:
		print(" -", str(track))
		if track.devices:
			print("    ", "devices:")
			for device in track.devices:
				print("     -", device)
		if track.active_clips:
			print("    ", "clips:")
			for clip in track.active_clips:
				print("     -", clip)
