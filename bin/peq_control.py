#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Módulo de control del EQ paramétrico Ecasound en FIRtro

 Uso en línea de comandos:

   peq_control.py "comando1 param1" "comando2 param2" ...

   comandoN puede ser

    - un comando nativo ecasound-iam (consultar la man)

    - un comando especial:
      PEQdump                  printa los filtros paramétricos en curso
      PEQdump2ecs              printa la estructura .ecs en curso
      PEQplot                  grafico del EQ en curso
      PEQbypass on|off|toggle  bypass del EQ
      PEQgain XX               ajusta la ganancia del EQ (primer plugin)
"""
# v1.0a:
#  Comprueba que Ecasound esté escuchando
# v1.1:
#  Corregido cargaPEQini cuando el INI tiene menos bloques de plugins que ecasound
#  Permite PEQdump sin ser el dueño del fichero /home/firtro/lspk/altavoz/peqdump.txt
# v1.1a:
#  Suprimido el sleep(0.1) de cargaPEQini
#  y cambiado sleep(0.02) antes 0.1 en PEQbypass (estos sleeps habría que depurarlos...)
# v1.1b
#  Se printan los mensajes intercalando  lineas en blanco para mejor lectura en la consola.

from os import path as os_path, remove as os_remove
from sys import path as sys_path, argv as sys_argv
from time import sleep
from ConfigParser import ConfigParser
import socket
import peq2png

# esto es para importar los modulos del FIRtro que siguen abajo
HOME = os_path.expanduser("~")
sys_path.append(HOME + "/bin")
from basepaths import config_folder, loudspeaker_folder
from getconfig import loudspeaker, ecasound_filters

# Usado solamente en PEQdefeat
status = ConfigParser()

# Solo se usa para el archivo temporal de volcado de EQ en curso (peqdump.txt)
altavoz_folder = loudspeaker_folder + loudspeaker

# --- AJUSTES DE LOS PARAMETRICOS ---
# Los valores de los filtros paramétricos los almacenaremos en un objeto ConfigParser (ini)
PEQs = ConfigParser()

# ---  ECASOUND  ------
def ecanet(comando):
    """ para enviar comandos a Ecasound y recibir resultados
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 2868))
    s.send(comando + "\r\n")
    data = s.recv(8192)
    s.close()
    return data

def leeCanalPEQini(fileName, channel):
    """ Se lee el archivo externo XXXX.peq con la configuracion de PEQs para ambos canales.
        Se devuelven dos cadenas de parámetros para conseguir los 4 + 4 paramétricos por canal.
    """
    PEQs.read(fileName)

    cad = ""
    for filtro in PEQs.options(channel):
        cad += "," + ",".join(PEQs.get(channel, filtro).split())

    return cad[1:]  # global...filtros_1-4...filtros_5-8 (quitamos la primera coma del join)

def cargaPEQini(archivoPEQini):
    """ recarga al vuelo los plugins de Ecasound releyendo
        un archivo XXXXXX.peq indicado (de tipo INI)
    """
    for channel in ["left","right"]:
        # leemos el canal dentro del archivo XXXXXX.peq
        listaParamsPlugins = leeCanalPEQini(archivoPEQini, channel).split(",")

        # seleccionamos el canal en Ecasound
        ecanet("c-select " + channel)

        # consultamos la relacion de plugins (cop) encadenados en el canal ecasound
        plugins = ecanet("cop-list").split("\r\n")[1].split(",")
        # recorremos los plugins (se seleccionan por su número de orden)
        for n in range(len(plugins)):

            # seleccionamos el plugin a modificar
            cop = n + 1 # ecasound numera desde "1"
            ecanet("cop-select " + str(cop))

            # sobreescribimos el ajuste de cada paramétrico de ecasound con lo que tenga el INI
            for pos in range(1,19): # cada plugin tiene 18 parámetros (2 globales y 4x4 de los filtros)
                # (!) por si el pop* se agota antes que los posibles filtros admitidos en ecasound
                if listaParamsPlugins:
                    ecanet("cop-set " + str(cop) + "," + str(pos) + "," + listaParamsPlugins.pop(0)) #(*)

    #sleep(.1) # valor experimental ya no hace falta v1.1a
    print "\n(peq_control) Se ha cargado en Ecasound el archivo: " + archivoPEQini.split("/")[-1]
    print "(peq_control) Recuerda revisar la Ganancia global del primer plugin.\n"
    try:
        if len(listaParamsPlugins) > 0:
            print "\n(peq_control) La lista de filtros excede la capacidad de " + str(len(plugins)) \
                  + " plugins de Ecasound\n"
    except:
        pass

def PEQdefeat():
    """ carga una ChainSetup externa (PEQ_defeat_FSAMPLING.ecs con los parametricos "a cero"
        (!!!) OjO habrá desconexión de los puertos de jack que entraban a ecasound.
    """
    status.read(config_folder + "/status")
    fs = status.get("general", "fs")
    bandasPEQ = ecasound_filters

    ecsDefeatFile = config_folder + "PEQx" + bandasPEQ + "_defeat_" + fs + ".ecs"
    if os_path.isfile(ecsDefeatFile):
        ecanet("cs-disconnect")
        ecanet("cs-remove")
        ecanet("cs-load " + ecsDefeatFile)
        ecanet("cs-connect")
        ecanet("start")
        # printamos:
        print "\n(peq_control) Ecasound ha cargado el archivo: " + ecsDefeatFile + "\n"
    else:
        print "\n(peq_control) ERROR accediendo al archivo: " + ecsDefeatFile + "\n"
        return False

def PEQgain(level):
    """ ajuste de ganacia del ecualizador en la primera etapa de plugin
    """
    for chain in ("left", "right"):
        ecanet("c-select " + chain) # selecc del canal
        ecanet("cop-select 1")      # selecc segunda etapa de filtros
        ecanet("copp-select 2")     # seleccion de la Gain global
        ecanet("copp-set " + level) # ajuste

def PEQbypass(mode):
    """ mode: on | off | toggle
    """
    for chain in ("left", "right"):
        ecanet("c-select " + chain)
        ecanet("c-bypass " + mode)
        sleep(.02) # experimental, es necesario

    for chain in ecanet("c-status").replace("[selected] ", "").split("\n")[2:4]:
        tmp = ""
        if "bypass" in chain.split()[2]:
            tmp = chain.split()[2]
        print " ".join(chain.split()[:2]) + " " + tmp

def PEQdump(fname=None):
    dump = ""
    dump += "\n# " + "Active".rjust(8) + "Freq".rjust(9) + "BW".rjust(7) + "Gain".rjust(8) + "\n"
    tmp = ecanet("cs-status").split("\n")

    # el canal L está en el campo 7 de tmp y el R en el campo 8.
    for pos in (7,8):
        chain = tmp[pos].split(" ")
        dump += "\n" + chain[3].replace('":',']').replace('"','[') + "\n"  # el nombre de la chain = canal.
        pluginNum = 1
        filterNum = 1
        for n in range(len(chain)): # recorremos los campos de la chain
            if "eli:" in chain[n]:  # es un plugin
                dump += auxPEQdump(chain[n], pluginNum, filterNum)    # lo destripamos
                pluginNum += 1
                filterNum += 4

    if fname:
        try:
            f = open(fname, "w")
            f.write(dump)
            f.close()
        except:
            print "\n(peq_control) (!) no se ha podido volcar al archivo " + fname + "\n"

    return dump

def auxPEQdump(plugin, pluginNum, filterNum):
    tmp = ""
    p = plugin.split(",")
    tmp += "global"+str(pluginNum)+" = " + p[ 1][0].rjust(2) + p[ 2].rjust(24) + "\n"
    tmp += "f"+str(filterNum+0).ljust(2)+" =     " + p[ 3][0].rjust(2) + p[ 4].rjust(9) + p[ 5].rjust(7) + p[ 6].rjust(8) + "\n"
    tmp += "f"+str(filterNum+1).ljust(2)+" =     " + p[ 7][0].rjust(2) + p[ 8].rjust(9) + p[ 9].rjust(7) + p[10].rjust(8) + "\n"
    tmp += "f"+str(filterNum+2).ljust(2)+" =     " + p[11][0].rjust(2) + p[12].rjust(9) + p[13].rjust(7) + p[14].rjust(8) + "\n"
    tmp += "f"+str(filterNum+3).ljust(2)+" =     " + p[15][0].rjust(2) + p[16].rjust(9) + p[17].rjust(7) + p[18].rjust(8) + "\n"
    return tmp

def PEQdump2ecs():
    ecanet("cs-save-as /home/firtro/tmp.ecs")
    f = open("/home/firtro/tmp.ecs", "r")
    print f.read()
    os_remove("/home/firtro/tmp.ecs")

if __name__ == '__main__':

    try:
        ecanet("") # comprobamos que Ecasound esté escuchando
    except:
        print "(!) ECASOUND server not running"

    dumpfile = altavoz_folder + "/peqdump.txt"

    # si ejecutamos desde linea de comando podemos pasar uno o más comandos a Ecasoud
    if len(sys_argv) > 1:
        comandos = sys_argv[1:]
        for comando in comandos: # recorremos la lista de comandos
            if not("PEQ" in comando):
                print ecanet(comando)
            else:
                if comando == "PEQdump":
                    print PEQdump(dumpfile)
                elif comando == "PEQplot":
                    PEQdump(dumpfile)
                    peq2png.main(dumpfile, ploteaT=True)
                elif comando == "PEQdump2ecs":
                    PEQdump2ecs()
                elif "PEQbypass" in comando:
                    try:
                        PEQbypass(comando.split()[1])
                    except:
                        print "falta parámetro on | off | toggle"
                elif "PEQgain" in comando:
                    try:
                        gain = comando.split()[1]
                        PEQgain(gain)
                        # PEQdump()
                    except:
                        print "falta ganacia en dB"
                else:
                    print "(!) error en comando " + comando
                    print __doc__
    else:
        print __doc__

