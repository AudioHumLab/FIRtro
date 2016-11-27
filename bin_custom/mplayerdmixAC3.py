#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""
    http://www.mplayerhq.hu/DOCS/HTML/en/advaudio-channels.html
    http://www.mplayerhq.hu/DOCS/tech/slave.txt
    http://people.iola.dk/arj/2010/02/27/channel-downmixing-in-mplayer/
    
    uso:
        mplayerdmixAC3.py [on|off]
"""
# v0.1beta

from subprocess import Popen
from sys import argv as sys_argv

# canales del downmix:
panCH = "L", "R"

# panning:
#        L    R
FLpan = 0.4, 0.0
FRpan = 0.0, 0.4
RLpan = 0.2, 0.0
RRpan = 0.0, 0.2
CEpan = 0.1, 0.1
SWpan = 0.4, 0.4

def panAC3():
    f =   [":".join([str(x) for x in FLpan])]
    f +=  [":".join([str(x) for x in FRpan])]
    f +=  [":".join([str(x) for x in RLpan])]
    f +=  [":".join([str(x) for x in RRpan])]
    f +=  [":".join([str(x) for x in CEpan])]
    f +=  [":".join([str(x) for x in SWpan])]
    return "pan=" + str(len(panCH)) + ":" + ":".join(f)

if __name__ == "__main__":
    if sys_argv[1:]:
        # borramos cualquier filtro previo
        Popen('echo "af_clr" > /home/firtro/tdt_fifo', shell=True)
        if sys_argv[1] == "on":
            # añadimos el filtro pan que hace el downmix
            Popen('echo "af_add ' + panAC3() + '" > /home/firtro/tdt_fifo', shell=True)
    else:
        print __doc__    
