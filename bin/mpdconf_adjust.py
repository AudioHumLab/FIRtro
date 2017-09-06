#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    v1.2
    modulo auxiliar para reconfigurar ~/.mpdconf con los puertos jack
    adecuados a la configuracion de FIRtro: brutefir o ecasound

    uso desde linea de comandos:
        mpdconf_adjust.py  brutefir|ecasound|dummy
"""
# v1.1:
# se añade la revisión del archivo ~/.mpdconf modificado
# v1.2:
# se incluye dummy de jack

from os import path as os_path
from sys import argv as sys_argv
import getconfig

HOME = os_path.expanduser("~")

def _lee(file):
    f = open(file, "r")
    lineas = f.read().split("\n")
    f.close()
    return lineas

def _revisa(lineas):
    """ En cualquiera de los siguientes casos esta función devolverá False:

        - si no existiera la opción destination_ports en la salida a JACK,
          ya que MPD prodría autoconectarse a las vías system:playback_X

        - si destination_ports no se correspondiera con los puertos de brutefir o ecasound
          definidos en audio/config.
    """
    puertos_son_correctos = False
    puertos = ""

    # tomamos nota de cualquier línea 'destination_ports ...' encontrada
    for linea in lineas:
        if not '#' in linea:
            if 'destination_ports' in linea:
                puertos += linea.split('"')[1]

    # los puertos de .mpdconf van separados por comas, debemos separarlos con espacios
    # antes de compararlos con los puertos brutefir/ecasound de audio/config
    puertos =  puertos.replace(',', ' ' )

    if puertos == getconfig.brutefir_ports or puertos == getconfig.ecasound_ports \
       or puertos == getconfig.dummy_ports:
        puertos_son_correctos = True
    else:
        print "(mpdconf_adjust) (!) ERROR en .mpdconf. Revisar destination ports:", puertos

    return puertos_son_correctos

def _busca_firtro_ports_deseados(opcion):

    if opcion == "brutefir":
        # nota: insertamos una coma en la lista puertos separados por espacios
        #       que nos proporciona getgonfig según los definidos en audio/config
        firtro_ports = getconfig.brutefir_ports.replace(" ", ",")

    elif opcion == "ecasound":
        firtro_ports = getconfig.ecasound_ports.replace(" ", ",")

    elif opcion == "dummy":
        firtro_ports = getconfig.dummy_ports.replace(" ", ",")

    else:
        return False

    return firtro_ports

def modifica_jack_destination_ports(opcion):

    firtro_ports = _busca_firtro_ports_deseados(opcion)
    if not firtro_ports:
        return False

    # leemos .mpdconf
    lineas = _lee(HOME + "/.mpdconf")

    # y lo sobreescribimos
    f = open(HOME + "/.mpdconf", "w")
    #f = open(HOME + "/prueba", "w") # DEBUG

    is_section_output = False
    is_jack_output    = False
    hay_cambios = False

    # repasamos línea a línea:
    for linea in lineas:

        # solo analizamos las no comentadas
        if not '#' in linea:

            if linea.replace(' ', '') == 'audio_output{':
                is_section_output = True

            if is_section_output and linea.replace(' ', '') == 'type"jack"':
                is_jack_output = True

            if linea.replace(' ', '') == '}':
                is_section_output = False
                is_jack_output    = False

            if 'destination_ports' in linea and is_jack_output:
                # tomamos la primera parte de la linea y
                # la completamos añadiendo lon nuevos puertos
                linea = linea.split('"')[0].rstrip() + ' "' + firtro_ports + '"'
                hay_cambios = True

        # reescribimos cada linea como en el original, ahora con los nuevos puertos.
        f.write(linea + "\n")

    f.close()

    # finalmente revisamos el archivo modificado
    if _revisa(_lee(HOME + "/.mpdconf")):
    #if _revisa(_lee(HOME + "/prueba")): # DEBUG
        return True
    else:
        return False


# opcionalmente podemos usar el módulo desde un terminal
if __name__ == "__main__":

    if len(sys_argv) > 1:
        if modifica_jack_destination_ports(sys_argv[1]):
            print "done"
        else:
            print "error"

    else:
        print __doc__

