#!/usr/bin/env python3

#------------------------------------------------------------------------
# pylive: ex-live-scan.py
#
# Demonstrates scanning the live set and outputs its structure.
#------------------------------------------------------------------------
from live import *

import logging

logging.basicConfig(format="%(asctime)-15s %(message)s")
logging.getLogger("live").setLevel(logging.INFO)

#------------------------------------------------------------------------
# Scanning a set with clip names and devices gives a more comprehensive
# overview of the set, but takes significantly longer.
#------------------------------------------------------------------------
set = Set()
set.scan(scan_clip_names=True, scan_devices=True)
set.dump()

