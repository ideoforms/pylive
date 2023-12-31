#!/usr/bin/env python3

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

def main():
    #------------------------------------------------------------------------
    # Scan the contents of the Live set, and start it playing.
    #------------------------------------------------------------------------
    set = live.Set(scan=True)
    set.dump()
    set.start_playing()

    #------------------------------------------------------------------------
    # Set 1-beat (quarter-note) quantization.
    #------------------------------------------------------------------------
    set.clip_trigger_quantization = 7

    #------------------------------------------------------------------------
    # Select the first track.
    #------------------------------------------------------------------------
    track = set.tracks[0]
    if len(track.active_clips) == 0:
        raise LiveException("Please open a Live set with at least one clip in the first track")

    #------------------------------------------------------------------------
    # track.clips is a list of all clip slots on the given Track, some of
    # which may be None (as a slot may be empty).
    #
    # Instead, we use track.active_clips, which returns a list of all
    # Clip objects on the Track.
    #------------------------------------------------------------------------
    clip_index = random.randrange(0, len(track.active_clips))
    track.active_clips[clip_index].play()

    #------------------------------------------------------------------------
    # Now, set up an infinite loop in which we play the following or
    # previous clip once per beat. 
    #------------------------------------------------------------------------
    while True:
        set.wait_for_next_beat()

        #------------------------------------------------------------------------
        # Skip to the next or previous populated clip.
        #------------------------------------------------------------------------
        if random.uniform(0, 1) < 0.5:
            clip_index = (clip_index + 1)
        else:
            clip_index = (clip_index - 1)

        clip_index = clip_index % len(track.active_clips)
        clip = track.active_clips[clip_index]
        clip.play()

if __name__ == "__main__":
    main()
