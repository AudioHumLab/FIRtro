#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import curses # no usado
import os
from subprocess import check_output, Popen
fifo = "/home/firtro/info_fifo"

# Tomamos nota de las líneas y columnas del terminal:
tlines = int(check_output("tput lines", shell=True))
tcols  = int(check_output("tput cols", shell=True))
# Nota: el terminal de la app SSH Term Pro del iPad
#       tiene 16x38 con la máxima fontsize=42.
#       Un pantalla de Spotify puede ocupar a lo sumo 10 lineas,
#       por tanto disponemos de 6 lineas extra para acomodar
#       el estado de FIRtro

def sublineas(linea, lmax):
    cachos = linea.split()
    sls = [] # sublineas
    while cachos:
        tmp = cachos.pop(0) + " "
        while cachos and len(tmp + cachos[0]) < lmax:
            tmp += cachos.pop(0) + " "
        sls.append(tmp)
    return sls

def mainLoop():

    while True:
        # Se completará la lectura de la fifo cada vez
        # que se haya escrito EOF en ella.
        # NOTA: El contenido de la FIFO es el estado de FIRtro enmarcado
        #       en guiones "--------------------------",
        #       seguido del estado del Player en curso.
        f = open(fifo, "r")
        tmp = f.read()
        f.close()
        lineas = tmp.split("\n")

        os.system("clear")      # borramos el terminal

        c = 0
        while lineas:
            linea = lineas.pop(0).center(tcols)   # vamos extrayendo lineas
            if "--------" in linea:
                c += 1
            if c < 2:
                print linea.center(tcols)
            else:
                if not "--------" in linea:
                    print
                for sl in sublineas(linea, lmax=tcols):
                    print sl.center(tcols)

def mataotros():
    tmp = check_output( "ps -ef | grep python | grep printinfofifo.py", \
                       shell=True ).split("\n")[:-1]
    # eliminamos el pid del grep
    tmp = [ x for x in tmp if not "grep" in x]
    # nos quedamos solo con el nº de pid que es la segunda columna
    pids = [x.split()[1] for x in tmp]
    # lo pasamos a enteros
    pids = [int(x) for x in pids]
    if pids:
        pids.remove(max(pids))  # quitamos el último pid que es el propio
    for pid in pids:            # y matamos el resto
        Popen("kill " + str(pid), shell =True)

if __name__ == "__main__":

    # Como la fifo solo puede leerla un proceso, debemos terminar
    # cualquier instancia previa de este programa:
    mataotros()

    # Bucle de lectura de la fifo y printado en el terminal
    mainLoop()

