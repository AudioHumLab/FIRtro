#!/usr/bin/env python
"""
    Script para visualizar el estado de las tarjetas alsa.
    Admite una string como filtro de tarjeta a listar.
"""
# cat /proc/asound/CODEC/pcm0p/sub0/hw_params
# access: MMAP_INTERLEAVED
# format: S16_LE
# subformat: STD
# channels: 2
# rate: 48000 (48000/1)
# period_size: 4096
# buffer_size: 12288

import os,sys

filtro = ""
if len(sys.argv) > 1:
    if "help" in sys.argv[1]:
        print __doc__
        exit()
    else:
        filtro = sys.argv[1]


f = open("/proc/asound/cards", "r")
conte = f.readlines()
f.close()
tarjetas = []

for linea in conte:
    if "[" in linea:
        t_index = linea.split("[")[0].strip()
        t_name  = "["+linea.split("[")[1].split("]")[0] + "]"
        tarjetas.append([t_index, t_name])

if tarjetas:
    # cabecera
    print " card                         access              format subformat ch   rate               period  buffer"
    #      [CODEC          ] pcm0c sub0 ['MMAP_INTERLEAVED', 'S16_LE', 'STD', '2', '48000 (48000/1)', '4096', '12288']

for tarjeta in tarjetas:
    t_dir = "/proc/asound/" + tarjeta[1].split("[")[1].split("]")[0].strip()
    t_files = os.listdir(t_dir)
    for file in t_files:
        if file[:3] == "pcm" and filtro in tarjeta[1]:
            pcm = file
            pcm_files = os.listdir(t_dir + "/" + pcm)
            for file in pcm_files:
                if file[:3] == "sub":
                    sub = file
                    f=open(t_dir + "/" + pcm + "/" + sub + "/hw_params", "r")
                    hw_params = f.readlines()
                    f.close()
                    lista_hw_simple = []
                    for cosa in hw_params:
                        if ":" in cosa:
                            lista_hw_simple.append(cosa.split(":")[1].strip())
                        else:
                            lista_hw_simple.append(cosa.strip())
                    print tarjeta[1].rjust(12, "_"), pcm, sub, lista_hw_simple
