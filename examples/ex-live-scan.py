#!/usr/bin/env python3

#------------------------------------------------------------------------
# pylive: ex-live-scan.py
#
# Connects to the Live set and prints its structure.
#------------------------------------------------------------------------
from live import *

import logging

logging.basicConfig(format="%(asctime)-15s %(message)s")
logging.getLogger("live").setLevel(logging.INFO)

set = Set(scan=True)
set.dump()

