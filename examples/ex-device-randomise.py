#!/usr/bin/env python3

#------------------------------------------------------------------------
# pylive: ex-parameter-randomise.py
#
# Randomises the parameters of every device found in the set.
#------------------------------------------------------------------------
from live import *

import logging

logging.basicConfig(format="%(asctime)-15s %(message)s")
logging.getLogger("live").setLevel(logging.INFO)

def main():
    set = Set()
    set.scan()
    for track in set.tracks:
        for device in track.devices:
            print("%s: Randomising %d parameters" % (device, len(device.parameters)))
            for parameter in device.parameters:
                print(" - %s" % parameter)
                if parameter.name == "Device On":
                    parameter.value = True
                else:
                    parameter.randomise()
            
if __name__ == "__main__":
    main()
