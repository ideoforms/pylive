# PyLive

## Introduction

PyLive is a framework for controlling Ableton Live from a standalone Python script, mediated via Open Sound Control.

## Requirements

* [Ableton Live 7+](http://www.ableton.com/live) with [LiveOSC](http://livecontrol.q3f.org/ableton-liveapi/liveosc/) MIDI Remote script
* [Python 2.6+](http://www.python.org)
* [PyOSC](https://trac.v2.nl/wiki/pyOSC) package

## Usage

	import live

	set = live.Set()
	set.scan(scan_clip_names = True)
	set.tempo = 110.0

	track = set.tracks[0]
	print "track name %s" % track.name

	clip = track.clips[0]
	print "clip name %s, length %d beats" % (clip.name, clip.length)
	clip.play()

## Overview

## Classes

* **Set**: Represents a single Ableton Live set in its entirety. 
* **Track**: A single Live track object. Contains Device objects. May be a member of a Group.
* **Group**: A grouped set of one or more Track objects.
* **Device**: An instrument or audio effect residing within a Track. Contains a number of Parameters.
* **Parameter**: An individual control parameter of a Device, with a fixed range and variable value.

