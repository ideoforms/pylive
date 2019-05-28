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
print("track name %s" % track.name)

clip = track.clips[0]
print("clip name %s, length %d beats" % (clip.name, clip.length))
clip.play()

"""

__version__ = "0.2.0"
__author__ = "Daniel Jones <http://www.erase.net/>"
__all__ = [ "Query", "Set", "Track", "Group", "Clip", "Device", "Parameter", "Scene" ]

debug = False

from .object import *
from .constants import *
from .set import *
from .query import *
from .track import *
from .group import *
from .clip import *
from .scene import *
from .device import *
from .parameter import *
from .exceptions import *
