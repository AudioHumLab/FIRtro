#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
import subprocess
import numpy as np

def dBs2percent(dBs):
    return str(int(10**(dBs/20.0) * 100))

if __name__ == '__main__':

    if len(sys.argv) > 1:
        dBs = int(sys.argv[1])
        os.system("mpc -p 7700 volume " + dBs2percent(dBs))
    else:
        tmp = subprocess.check_output("mpc -p 7700 volume".split())
        tmp = tmp.split("%")[0].split(":")[-1].strip()
        dBs = 20 *np.log(int(tmp)/100.0)
        print tmp + "%", str(int(dBs)) + " dB"
