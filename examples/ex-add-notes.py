#!/usr/bin/env python3

#------------------------------------------------------------------------
# pylive: ex-add-notes
#
# Add 16 randomly-generated notes to a clip.
# The first track must be a MIDI track.
#------------------------------------------------------------------------

import live
import time
import random

def main():
    #--------------------------------------------------------------------------------
    # Connect to the Live set.
    #--------------------------------------------------------------------------------
    set = live.Set()
    set.scan()

    #--------------------------------------------------------------------------------
    # Connect to the Live set.
    #--------------------------------------------------------------------------------
    track = set.tracks[0]
    if not track.is_midi_track:
        raise ValueError("First track must be a MIDI track")
    clip = set.tracks[0].clips[0]
    if clip is None:
        clip = track.create_clip(0, 4)
    if not clip.is_midi_clip:
        raise ValueError("Clip at [0, 0] must be a MIDI clip")

    print("Populating clip [0, 0] with random notes")
    for n in range(32):
        note = generate_random_note(clip)
        print(" - Adding note %d at time %.2f" % (note[0], note[1]))
        clip.add_note(*note)

def generate_random_note(clip: live.Clip):
    #--------------------------------------------------------------------------------
    # Generate a random note in a minor scale.
    #--------------------------------------------------------------------------------
    scale = (0, 2, 3, 5, 7, 8, 10)
    degree = random.choice(scale)
    octave = random.randrange(3)
    fundamental = 60
    pitch = fundamental + (octave * 12) + degree

    #--------------------------------------------------------------------------------
    # Generate a random start time, rounded to the nearest note
    #--------------------------------------------------------------------------------
    start_time = int(random.uniform(0, clip.length - 0.5) * 4) / 4

    duration = 0.5
    velocity = random.randrange(0, 127)
    mute = False

    return pitch, start_time, duration, velocity, mute


if __name__ == "__main__":
    main()
