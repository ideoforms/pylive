# PyLive

## Introduction

PyLive is a framework for controlling Ableton Live from a standalone Python script, mediated via Open Sound Control.

## Requirements

* [Ableton Live 7+](http://www.ableton.com/live) with the [LiveOSC](http://livecontrol.q3f.org/ableton-liveapi/liveosc/) MIDI Remote script
* [Python 2.6+](http://www.python.org)
* [PyOSC](https://trac.v2.nl/wiki/pyOSC)

## Usage

	import live, random

	set = live.Set()
	set.scan(scan_clip_names = True, scan_devices = True)
	set.tempo = 110.0

	track = set.tracks[0]
	print "track name %s" % track.name

	clip = track.clips[0]
	print "clip name %s, length %d beats" % (clip.name, clip.length)
	clip.play()

	set.wait_for_next_beat()
	clip.get_next_clip().play()

	device = track.devices[0]
	parameter = random.choice(device.parameters)
	parameter.value = random.uniform(parameter.minimum, parameter.maximum)

## Overview

To begin interacting with an Ableton Live set, the typical workflow is as follows. Live should normally be running on localhost, with [LiveOSC](http://livecontrol.q3f.org/ableton-liveapi/liveosc/) enabled as a Control Surface.

* Create a `live.Set` object.
* Call `set.scan()`, which queries Live for an index of tracks, clip statuses, and (optionally) clip names and devices
* Interact with Live by setting and getting properties on your `Set`:
** `set.tempo`, `set.time`, `set.overdub` are global Set properties
** `set.tracks` is a list of Track objects
** `set.tracks[N].name`, `set.tracks[N].mute`, are Track properties
** `set.tracks[N].clips` is a list of Clip objects (with empty slots containing `None`)
** `set.tracks[N].devices` is a list of Device objects
** `set.tracks[N].devices[M].parameters` is a list of Parameter objects

Getters and setters use Python's `@property` idiom, meaning that accessing `set.tempo` will query or update your Live set.

If you know that no other processes will interact with Live, set `set.caching = True` to cache properties such as tempo. This will query the Live set on the first instance, and subsequently return locally-stored values.

For further help, see `pydoc live`.

## Classes

* **Set**: Represents a single Ableton Live set in its entirety. 
* **Track**: A single Live track object. Contains Device objects. May be a member of a Group.
* **Group**: A grouped set of one or more Track objects.
* **Device**: An instrument or audio effect residing within a Track. Contains a number of Parameters.
* **Parameter**: An individual control parameter of a Device, with a fixed range and variable value.

