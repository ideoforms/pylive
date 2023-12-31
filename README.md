# PyLive

PyLive is a framework for querying and controlling Ableton Live from a standalone Python script, mediated via Open Sound Control. Internally, it uses the same API as a Live Control Surface, which means it can do anything that a hardware control surface can do, including:

 - query and modify global parameters such as tempo, volume, pan, quantize, arrangement time
 - query and modify properties of tracks, clips, scenes and devices
 - trigger and stop clips and scenes

It can perform many of the operations described in the [AbletonOSC API](https://github.com/ideoforms/AbletonOSC). More comprehensive feature coverage is a work-in-progress.

If you are looking simply to send MIDI messages to Live, this module is not what you want. Instead, try setting up a [virtual MIDI bus](https://help.ableton.com/hc/en-us/articles/209774225-How-to-setup-a-virtual-MIDI-bus) and using [isobar](https://ideoforms.github.io/isobar/) to generate MIDI sequences.

**Note for legacy users:** As of 2023, pylive has been updated to to interface exclusively with [AbletonOSC](https://github.com/ideoforms/AbletonOSC) for Live 11 support. Legacy LiveOSC is no longer supported beyond [v0.2.2](https://github.com/ideoforms/pylive/releases/tag/v0.2.2).

## Requirements

* [Ableton Live 11+](http://www.ableton.com/live)
* [Python 3.7+](http://www.python.org)
* [AbletonOSC](https://github.com/ideoforms/AbletonOSC)

## Installation

From PyPi:

```
pip3 install pylive
```

Or to install the latest (pre-release) code from git:
```
git clone https://github.com/ideoforms/pylive.git
cd pylive
python3 setup.py install
```

To check that pylive is communicating successfully with Ableton Live, try running one of the [examples](examples), or run the test suite with:
```
python3 setup.py test
```

## Usage

```python
#------------------------------------------------------------------------
# Basic example of pylive usage: connect to the Live set, trigger a clip,
# and modulate some device parameters.
#------------------------------------------------------------------------
import live
import random

#------------------------------------------------------------------------
# Query the set's contents, and set its tempo to 110bpm.
#------------------------------------------------------------------------
set = live.Set(scan=True)
set.tempo = 110.0

#------------------------------------------------------------------------
# Each Set contains a list of Track objects.
#------------------------------------------------------------------------
track = set.tracks[0]
print("Track name '%s'" % track.name)

#------------------------------------------------------------------------
# Each Track contains a list of Clip objects.
#------------------------------------------------------------------------
clip = track.clips[0]
print("Clip name '%s', length %d beats" % (clip.name, clip.length))
clip.play()

#------------------------------------------------------------------------
# Mdulate the parameters of a Device object.
#------------------------------------------------------------------------
device = track.devices[0]
parameter = random.choice(device.parameters)
parameter.value = random.uniform(parameter.min, parameter.max)
print("Randomising parameter %s of device %s" % (parameter, device))
```

## Overview

To begin interacting with an Ableton Live set, the typical workflow is as follows. Live should normally be running on localhost, with LiveOSC enabled as a Control Surface.

* Create a `live.Set` object, passing `scan=True` to automatically index the tracks, clips and devices within the set
* Interact with Live by setting and getting properties on your `Set`:
  * `set.tempo`, `set.time`, `set.overdub` are global Set properties
  * `set.tracks` is a list of Track objects
  * `set.tracks[N].name`, `set.tracks[N].mute`, are Track properties
  * `set.tracks[N].clips` is a list of Clip objects (with empty slots containing `None`)
  * `set.tracks[N].devices` is a list of Device objects
  * `set.tracks[N].devices[M].parameters` is a list of Parameter objects

Getters and setters use Python's `@property` idiom, meaning that accessing `set.tempo` will query or update your Live set.

If you know that no other processes will interact with Live, set `set.caching = True` to cache properties such as tempo. This will query the Live set on the first instance, and subsequently return locally-stored values.

For further help, see `pydoc live`.

## Classes

* `Set`: Represents a single Ableton Live set in its entirety. 
* `Track`: A single Live track object. Contains `Device` and `Clip` objects. May be a member of a `Group`.
* `Group`: A grouped set of one or more `Track` objects.
* `Device`: An instrument or audio effect residing within a `Track`. Contains a number of `Parameter` objects.
* `Parameter`: An individual control parameter of a `Device`, with a fixed range and variable value.

## Limitations

Note that pylive is not intended for sending MIDI note events or control messages to a set. For MIDI controls, use a separate module such as [mido](https://mido.readthedocs.io).
