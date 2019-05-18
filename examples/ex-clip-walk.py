#!/usr/local/bin/python

#------------------------------------------------------------------------
# pylive: ex-clip-walk.py
#
# Demonstrates triggering clips by "walking" between clips in a
# single track.
#
# Requires a Live set with multiple clips in its first track.
#------------------------------------------------------------------------

import live
import time
import threading
import random
import logging

logging.basicConfig(format="%(asctime)-15s %(message)s")
logging.getLogger("live").setLevel(logging.INFO)

#------------------------------------------------------------------------
# Scan the contents of the Live set, and start it playing.
#------------------------------------------------------------------------
set = live.Set()
set.scan()
set.dump()
set.play()

#------------------------------------------------------------------------
# Select the first track.
#------------------------------------------------------------------------
track = set.tracks[0]

#------------------------------------------------------------------------
# track.clips is a list of all clipslots on the given Track, some of
# which may be None (as a slot may be empty).
#
# Instead, we use track.active_clips, which returns a list of all
# Clip objects on the Track.
#------------------------------------------------------------------------
clip = random.choice(track.active_clips)

#------------------------------------------------------------------------
# Now, set up an infinite loop in which we play the following or
# previous Clip once per beat. Switch Live's quantization to "1 beat".
#------------------------------------------------------------------------
while True:
	set.wait_for_next_beat()
	# print("Playing clip: %s" % clip)

	#------------------------------------------------------------------------
	# wrap = True: Wrap between the last and first clips of the track.
	# allow_gaps = True: Jump over gaps between populated clips.
	#------------------------------------------------------------------------
	if random.uniform(0, 1) < 0.5:
		clip = clip.get_next_clip(wrap = True, allow_gaps = True)
	else:
		clip = clip.get_prev_clip(wrap = True, allow_gaps = True)

	clip.play()

