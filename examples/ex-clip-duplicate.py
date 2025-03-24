#!/usr/bin/env python3

#------------------------------------------------------------------------
# pylive: ex-clip-duplicate.py
#
# Demonstrates duplicating a clip to another scene.
#
# Requires a Live set with a clip in the first scene of the first track.
#------------------------------------------------------------------------
import live
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
    clip = track.clips[0]
    if clip is None:
        raise LiveException("Please open a Live set with a clip in scene one of the first track")

    if track.clips[1] is not None:
        raise LiveException("Please clear the second clip in the first track")

    clip.duplicate(1, 2)
    duplicate_clip = set.tracks[0].clips[1]
    clip.stop()
    duplicate_clip.play()


if __name__ == "__main__":
    main()
