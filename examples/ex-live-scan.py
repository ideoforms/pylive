#!/usr/local/bin/python

#------------------------------------------------------------------------
# pylive: ex-live-scan.py
#
# Demonstrates scanning the live set and outputs its structure.
#------------------------------------------------------------------------

from live import *

#------------------------------------------------------------------------
# Scanning a set with clip names and devices gives a more comprehensive
# overview of the set, but takes significantly longer.
#------------------------------------------------------------------------
set = Set()
set.scan(scan_clip_names = False, scan_devices = False, group_re = "[A-Z].\d{2} -.*")

for track in set.tracks:
	print str(track)
	for clip in track.active_clips:
		print "- %s" % clip
	for device in track.devices:
		print "- %s" % device
