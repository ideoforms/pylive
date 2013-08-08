"""

pylive
~~~~~~

A framework for controlling Ableton Live from a standalone Python script,
mediated via Open Sound Control.

USAGE
~~~~~

import live

set = live.Set()
set.scan(scan_clip_names = True)
set.tempo = 110.0

track = set.tracks[0]
print "track name %s" % track.name

clip = track.clips[0]
print "clip name %s, length %d beats" % (clip.name, clip.length)
clip.play()

"""

__version__ = "0.0.1"
__author__ = "Daniel Jones <http://www.erase.net/>"
__all__ = [ "Query", "Set", "Track", "Group", "Clip", "Device", "Parameter" ]

from live.object import *
from live.constants import *
from live.set import *
from live.query import *
from live.track import *
from live.group import *
from live.clip import *
from live.device import *
from live.parameter import *
