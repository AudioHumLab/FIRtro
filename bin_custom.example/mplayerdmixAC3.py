#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""
    Configura mplayer slave para hacer downmix de AC3 5.1

    uso:
            mplayerdmixAC3.py [on|off]
    nota:
            coeffs de downmix en ~/custom/userconfig.ini
            mplayer slave fifo:  ~/tdt_fifo
"""
# v0.1beta

from subprocess import Popen
from sys import argv as sys_argv
from ConfigParser import ConfigParser
import os
HOME = os.path.expanduser("~")

dmixINI = ConfigParser()
dmixINIpath = "/home/firtro/custom/userconfig.ini"
fifoPath = HOME + "/tdt_fifo"

def panAC3():
    #http://www.mplayerhq.hu/DOCS/HTML/en/advaudio-channels.html
    #http://www.mplayerhq.hu/DOCS/tech/slave.txt
    
    # leemos la sección ac3downmix de ~/custom/userconfig.ini
    # en la que estás definidos los % de  downmix
    dmixINI.read(dmixINIpath)
    try:
        FLpan = dmixINI.get("ac3downmix", "FL").split()
        FRpan = dmixINI.get("ac3downmix", "FR").split()
        SLpan = dmixINI.get("ac3downmix", "SL").split()
        SRpan = dmixINI.get("ac3downmix", "SR").split()
        CEpan = dmixINI.get("ac3downmix", "CE").split()
        SWpan = dmixINI.get("ac3downmix", "SW").split()
    except:
        return False

    f =   [":".join([str(x) for x in FLpan])]
    f +=  [":".join([str(x) for x in FRpan])]
    f +=  [":".join([str(x) for x in SLpan])]
    f +=  [":".join([str(x) for x in SRpan])]
    f +=  [":".join([str(x) for x in CEpan])]
    f +=  [":".join([str(x) for x in SWpan])]

    return "pan=2:" + ":".join(f)

if __name__ == "__main__":
    if sys_argv[1:]:
        # borramos cualquier filtro previo
        Popen('echo "af_clr" > ' + fifoPath, shell=True)
        if sys_argv[1] == "on":
            # añadimos el filtro pan que hace el downmix
            filtro = panAC3()
            if filtro:
                #print panAC3() # debug
                Popen('echo "af_add ' + filtro  + '" > ' + fifoPath, shell=True)
            else:
                print "No se localiza información de downmix en " + dmixINIpath
    else:
        print __doc__
