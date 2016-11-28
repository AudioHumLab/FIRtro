#!/usr/bin/env python
"""
    ecasignalview para FIRtro
    uso:
        ecasignalview.py [jackClient] (default: ecasound)
"""
import jack
from subprocess import call
from sys import argv as sys_argv, exit as sys_exit

def readable_ports(cli):
    """devuelve los puertos leibles de un cliente jack
    """
    c = []
    jack.attach("tmp")
    ports = jack.get_ports()
    for port in ports:
        if cli in port:
            if not jack.get_port_flags(port) % 2: # it is a readable port
                c.append(port)
    jack.detach()
    return c

if __name__ == "__main__":

    client = "ecasound" # default

    if sys_argv[1:]:
        client = sys_argv[1]
        if "-h" in client:
            print __doc__
            sys_exit()

    #print readable_ports(client) # debug
    channels = str(len(readable_ports(client)))
    # run ecasignaview:
    call("ecasignalview -f:f32," + channels + " jack," + client + "  null", shell=True)

